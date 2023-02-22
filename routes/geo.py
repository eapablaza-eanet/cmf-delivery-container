from app import app, __VERSION
from flask import jsonify,request

@app.route(f"{__VERSION}/direccion/<id>/updategeo", methods=['POST'])
def direccion(id):
    from models.gps.geocore import Direccion
    dir_ubic    = request.json.get('Direccion')
    #Av. Pdte. Eduardo Frei Montalva 5981, 8550187 Santiago, Conchalí, Región Metropolitana

    dir_upd  = Direccion.objects(id=id).first()
    if dir_upd is None:
        return jsonify({'Status': False, 'Msg': 'Direccion ID no encontrada' })
    
    dir_old = dir_upd.Direccion

    dir_upd.Direccion = dir_ubic
    dir_upd.save()
    
    dir_upd.BuscaGeoReferencia(force=True)

    dir_upd.Direccion = dir_old
    dir_upd.save()
    
    return jsonify({'GEOTransporte': True, 'Msg': f"Por > {dir_ubic}" })
