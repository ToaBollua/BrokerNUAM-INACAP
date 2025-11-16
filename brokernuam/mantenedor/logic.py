# mantenedor/logic.py
import csv
import io
from decimal import Decimal, InvalidOperation

def _to_float_safe(value):
    """
    Intenta convertir un valor a Decimal. Devuelve 0.0 si falla.
    Extraído de la lógica de carga masiva de tu compañero.
    """
    if value is None:
        return Decimal('0.0')
    try:
        # Reemplazar comas por puntos si es necesario (formato CSV)
        cleaned_value = str(value).strip().replace(',', '.')
        if cleaned_value == '':
            return Decimal('0.0')
        return Decimal(cleaned_value)
    except InvalidOperation:
        return Decimal('0.0')

def parse_csv(csv_file):
    """
    Parsea un archivo CSV en memoria y lo convierte en una lista de diccionarios.
    Extraído del views.py de tu compañero.
    """
    data = []
    try:
        decoded_file = csv_file.read().decode('utf-8-sig')
        io_string = io.StringIO(decoded_file)
        # Lee la primera línea para detectar el delimitador
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(io_string.read(1024))
        io_string.seek(0)
        
        reader = csv.reader(io_string, dialect=dialect)
        
        header = [h.strip() for h in next(reader)]
        
        for row in reader:
            if not any(row):  # Omitir filas vacías
                continue
            data.append(dict(zip(header, row)))
            
    except Exception as e:
        # En un sistema real, loggearíamos este error
        raise ValueError(f"Error al parsear el CSV: {e}")
    return data

def CalculoFactores(montos_data):
    """
    Lógica de negocio principal para convertir Montos a Factores.
    Extraído y adaptado del views.py de tu compañero.
    
    Valida que la suma de factores 8-16 no exceda 1.
    """
    
    monto = {}
    for i in range(1, 30):
        monto[i] = _to_float_safe(montos_data.get(f'amount{i}', 0))

    factores = {}
    
    # Asegurarse de que el monto1 (Divisor) no sea cero
    divisor = monto[1]
    if divisor == Decimal('0.0'):
        # Si el monto 1 es cero, todos los factores calculados son cero (o indefinidos)
        # Asignamos 0 a todos los factores 8-29
        for i in range(8, 30):
            factores[f'factor{i}'] = Decimal('0.0')
        
        # Validar la lógica de negocio incluso si el divisor es 0
        # (Suma de 0 es < 1, así que es válido)
        return factores # Retorna factores en cero

    factores['factor8'] = (monto[8] + monto[9] + monto[10] + monto[11] + monto[12] + monto[13]) / divisor
    factores['factor9'] = (monto[14] + monto[15]) / divisor
    factores['factor10'] = (monto[16] + monto[17] + monto[18]) / divisor
    factores['factor11'] = (monto[19] + monto[20] + monto[21]) / divisor
    factores['factor12'] = (monto[22] + monto[23]) / divisor
    factores['factor13'] = monto[24] / divisor
    factores['factor14'] = monto[25] / divisor
    factores['factor15'] = monto[26] / divisor
    factores['factor16'] = (monto[27] + monto[28]) / divisor
    
    for i in range(17, 30):
        factores[f'factor{i}'] = monto[i]

    suma_factores_8_16 = sum(factores.get(f'factor{i}', Decimal('0.0')) for i in range(8, 17))
    
    if round(suma_factores_8_16, 4) > 1:
        raise ValueError("La suma de factores 8 a 16 excede 1")

    return factores