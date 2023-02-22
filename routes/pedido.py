import logging
from app import app
from flask import jsonify, request

@app.route(f"{app.config.get('API_VERSION')}/pedido/en_curso", methods=['GET'])
def pedido_encurso():
    from models.delivery.pedido import DeliveryPedido
    data = DeliveryPedido.DeliverysEnCurso()
    return jsonify(data)

@app.route(f"{app.config.get('API_VERSION')}/pedido/<deliveryid>", methods=['GET'])
def pedido_detalle(deliveryid):
    from models.delivery.pedido import DeliveryPedido
    logging.info(f"Solicitando Info de {deliveryid}")
    if deliveryid == '0':
        return jsonify({})

    de_pe = DeliveryPedido.objects(id=deliveryid).first()
    return jsonify(de_pe.toJsonDetail())

@app.route(f"{app.config.get('API_VERSION')}/pedido/<deliveryid>/error", methods=['POST'])
def pedido_error(deliveryid):
    from models.delivery.pedido import DeliveryPedido
    de_pe = DeliveryPedido.objects(id=deliveryid).first()
    de_pe.CancelarSeguimiento('CANCELADO POR USUARIO')
    return jsonify({ "Pedido": de_pe.Pedido.Numero, "Delivery": deliveryid, "Status":"ERROR" })

@app.route(f"{app.config.get('API_VERSION')}/pedido/informe", methods=['POST'])
def pedido_informe():
    from models.delivery.pedido import DeliveryPedido
    fecha_inicio    = request.json.get('FechaInicio')
    fecha_fin       = request.json.get('FechaFin')
    logging.info(fecha_inicio)
    logging.info(fecha_fin)
    informe         = DeliveryPedido.Informe(fecha_inicio, fecha_fin)
    return jsonify(informe)
