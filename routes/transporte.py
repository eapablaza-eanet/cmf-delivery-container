from app import app, __VERSION
from flask import jsonify, request, send_file
from models.delivery.pedido import DeliveryPedido
from models.gps.transporte import Transporte

@app.route(f"{__VERSION}/transporte/status", methods=['POST'])
def transporte_status():
    detenidos = request.json.get('Detenido',False)
    en_planta = request.json.get('EnPlanta',True)
    en_entrega = request.json.get('EnEntrega',True)
    en_retorno = request.json.get('EnRetorno',False)
    sin_conexion = request.json.get('SinConexion',False)
    t = request.json.get('t','M')
    
    data = DeliveryPedido.StatusTransporte(sin_conexion, detenidos, en_planta, en_entrega, en_retorno, t)
    return jsonify(data)

@app.route(f"{__VERSION}/transporte/status/<patente>", methods=['POST'])
def transporte_status_patente(patente):
    t = request.json.get('t','M')
    data = DeliveryPedido.StatusTransporteByPatente(patente,t)
    return jsonify(data)

@app.route(f"{__VERSION}/transporte/imagen", methods=['GET'])
def transporte_img():
    patente = request.args.get('p', None)
    pedido = request.args.get('pe', None)
    tamano = request.args.get('t') #S/M/L/XL
    if tamano is None:
        tamano = 'M'

    tipo_imagen = request.args.get('ti') #1=si, 0=No
  
    img = Transporte.getImageCamion(tamano, patente, tipo_imagen, pedido)
    return send_file(img, mimetype='image/png')

@app.route(f"{__VERSION}/maps/imagen", methods=['GET'])
def maps_img():
    tamano = request.args.get('t') #D/O
    if tamano is None:
        tamano = 'M'

    tipo = request.args.get('f') #1=si, 0=No
    
    img = Transporte.getImage(tipo, tamano)
    return send_file(img, mimetype='image/png')

@app.route(f"{__VERSION}/transporte/geo/<lat>/<lng>", methods=['GET'])
def transporte_by_geo(lat, lng):
    t = request.args.get('t','M') #S/M/L/XL
    data = DeliveryPedido.get_by_pos(lat, lng, t)
    return jsonify(data)