import math
import matplotlib.pyplot as plt

def calculate_polygon(data):
    """Calcula as coordenadas X,Y do polígono a partir dos dados extraídos."""
    points = [(0, 0)] # Começa na origem
    current_x = 0
    current_y = 0
    
    tipo_medida = data.get("tipo_medida", "Azimute")
    
    for segmento in data.get("segmentos", []):
        dist = segmento.get("distancia_metros", 0)
        angulo_obj = segmento.get("angulo", {})
        
        graus = angulo_obj.get("graus", 0)
        minutos = angulo_obj.get("minutos", 0)
        segundos = angulo_obj.get("segundos", 0)
        quadrante = angulo_obj.get("quadrante")
        
        # 1. Converter tudo para graus decimais
        dec = graus + (minutos / 60) + (segundos / 3600)
        
        # 2. Converter para Azimute Universal (0-360) se for Rumo
        azimute_dec = dec
        if tipo_medida == "Rumo" and quadrante:
            q = quadrante.upper().strip()
            if q == 'NE':
                azimute_dec = dec
            elif q == 'SE':
                azimute_dec = 180 - dec
            elif q == 'SW':
                azimute_dec = 180 + dec
            elif q == 'NW':
                azimute_dec = 360 - dec
        
        # 3. Converter Azimute (Norte=0, Horário) para Trigonométrico Python (Leste=0, Anti-horário)
        trig_angle_deg = 90 - azimute_dec
        trig_angle_rad = math.radians(trig_angle_deg)
        
        # Calcular deslocamento
        dx = dist * math.cos(trig_angle_rad)
        dy = dist * math.sin(trig_angle_rad)
        
        current_x += dx
        current_y += dy
        
        points.append((current_x, current_y))
        
    return points

def plot_polygon(points):
    """Gera gráfico do polígono."""
    if not points:
        return None
        
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    
    # Fechar o polígono para o desenho
    x.append(x[0])
    y.append(y[0])
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(x, y, 'b-', linewidth=2)
    ax.fill(x, y, alpha=0.3)
    
    # Ajustar aspecto para não distorcer o terreno
    ax.set_aspect('equal', adjustable='box')
    ax.set_title("Pré-visualização da Geometria")
    ax.grid(True)
    
    return fig
