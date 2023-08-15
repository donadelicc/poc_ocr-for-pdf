from flask import Flask, request, render_template, send_from_directory, jsonify
from pdf2image import convert_from_path
import pytesseract
import os
from fpdf import FPDF
import glob

app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = '/home/donadelicc/mysite/uploads'
IMAGE_DIR = '/home/donadelicc/mysite/document_pages'
TXT_DIR = IMAGE_DIR

for folder in [UPLOAD_FOLDER, IMAGE_DIR, TXT_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

@app.route('/path_to_pdf_folder/<filename>')
def serve_pdf(filename):
    return send_from_directory(TXT_DIR, filename)


@app.route('/', methods=['GET', 'POST'])
def index():
    for old_file in glob.glob(os.path.join(TXT_DIR, "*.pdf")):
        os.remove(old_file)

    try:
        if request.method == 'POST':
            file = request.files.get('file')
            if not file or not file.filename.endswith('.pdf'):
                return jsonify({'error': 'Vennligst last opp en PDF-fil.'}), 400

            filename = os.path.join(UPLOAD_FOLDER, file.filename)        
            file.save(filename)

            if os.path.getsize(filename) == 0:
                return jsonify({'error': "Filen er tom. Vennligst last opp en gyldig PDF-fil."}), 400
        
            images = convert_from_path(filename)
            if not images:
                return jsonify({'error':"Kunne ikke konvertere PDF til bilder."}), 500

            pdf_output_filename = os.path.join(TXT_DIR, file.filename)
            os.remove(filename)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=11)
            pdf.set_auto_page_break(auto=True, margin=12)

            for i, image in enumerate(images):
                image_path = os.path.join(IMAGE_DIR, f'page_{i + 1}.png')
                image.save(image_path, 'PNG')
                text = pytesseract.image_to_string(image, lang='nor')
                pdf.multi_cell(190, 7, txt=text) 

                os.remove(image_path)
                
            pdf.output(pdf_output_filename)
            
            return jsonify({
                'filename': os.path.basename(pdf_output_filename)
            })
        
    except Exception as e:
        print(str(e))
        return f"En feil oppsto: {str(e)}", 500
        
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
