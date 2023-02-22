from datetime import datetime

class Turno():
    def __init__():
        pass

    def get_hora_despacho(turno, fecha_despacho, hora_despacho):
        if turno.strip() == '':
            turno = None

        if hora_despacho.strip() == '':
            hora_despacho = None
    
        [dia, mes, ano] = fecha_despacho.split('.')

        if turno is None and fecha_despacho is None:
            return datetime(int(ano), int(mes), int(dia), 12, 0) #Si no tiene turno que se despache a medio dia

        if hora_despacho is not None:
            [hora, minuto] = hora_despacho.split(':')
            return datetime(int(ano), int(mes), int(dia), int(hora), int(minuto))
        else:
            #Consulto por hora del turno
            hora_ft = 8
            return datetime(int(ano), int(mes), int(dia), int(hora_ft), 0)
            


