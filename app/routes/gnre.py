from flask import Blueprint, request, jsonify, current_app
import os

gnre_bp = Blueprint('gnre', __name__)

@gnre_bp.route('/upload-certificado', methods=['POST'])
def upload_certificado():
    file = request.files.get('certificado')
    if not file:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    upload_folder = os.environ.get('UPLOAD_FOLDER', './uploads')
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, file.filename)
    file.save(path)
    return jsonify({'mensagem': 'Certificado salvo com sucesso'})

@gnre_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'mensagem': 'API está funcionando'}), 200


