import math

def generate_cad_script(points, software="AutoCAD"):
    """Gera script .scr para o AutoCAD ou Ares Commander."""
    script = []
    
    def add_cmd(cmd):
        script.append(cmd)
    
    # Configuração Inicial
    add_cmd("_UNITS")
    add_cmd("2") # Decimal
    add_cmd("2") # Precision
    add_cmd("1") # Decimal Degrees
    add_cmd("2") # Precision
    add_cmd("0") # East
    add_cmd("N") # No clockwise
    
    add_cmd("_OSMODE")
    add_cmd("0")
    
    add_cmd("_-STYLE")
    add_cmd("Standard")
    add_cmd("Arial")
    add_cmd("0")
    add_cmd("1")
    add_cmd("0")
    add_cmd("_N")
    add_cmd("_N")
    
    # Identificadores de Pontos
    dists = [math.sqrt((points[i+1][0]-points[i][0])**2 + (points[i+1][1]-points[i][1])**2) for i in range(len(points) - 1)]
    avg_dist = sum(dists) / len(dists) if dists else 10
    text_height = max(0.2, avg_dist * 0.02)
    
    # Layer ARQ_PONTOS
    add_cmd("_-LAYER _N ARQ_PONTOS _C 1 ARQ_PONTOS _S ARQ_PONTOS")
    add_cmd("")
    
    for i, p in enumerate(points[:-1]): 
        label = f"P{i+1}"
        add_cmd(f"_TEXT {p[0]:.4f},{p[1]:.4f} {text_height:.4f} 0 {label}")
        add_cmd(f"_POINT {p[0]:.4f},{p[1]:.4f}")

    # Layer ARQ_PERIMETRO
    add_cmd("_-LAYER _N ARQ_PERIMETRO _C 4 ARQ_PERIMETRO _S ARQ_PERIMETRO")
    add_cmd("")
    
    add_cmd("_PLINE")
    for p in points:
        add_cmd(f"{p[0]:.4f},{p[1]:.4f}")
    add_cmd("C") # Close
    
    # Layer ARQ_COTAS
    add_cmd("_-LAYER _N ARQ_COTAS _C 2 ARQ_COTAS _S ARQ_COTAS")
    add_cmd("")
    
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i+1]
        mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        angle_deg = math.degrees(math.atan2(dy, dx))
        
        # Ajuste de leitura do texto
        if 90 < angle_deg <= 270 or -270 <= angle_deg < -90:
             angle_deg += 180
        
        add_cmd(f"_TEXT {mid_x:.4f},{mid_y:.4f} {text_height:.4f} {angle_deg:.4f} {dist:.2f}m")

    add_cmd("_ZOOM _E") 
    
    return "\n".join(script)
