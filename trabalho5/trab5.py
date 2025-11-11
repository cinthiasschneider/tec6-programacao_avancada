import pygame, sys, random, os, time, csv
from queue import PriorityQueue

# configuração e incialização do pygame
WIDTH, ROWS = 700, 50 
pygame.init(); pygame.font.init() 
WIN = pygame.display.set_mode((WIDTH, WIDTH + 30))
pygame.display.set_caption("Navegação")
FONT = pygame.font.Font(None, 24)

RED, GREEN, BLUE, YELLOW, WHITE, BLACK, PURPLE = (255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,255,255), (0,0,0), (128,0,128)
AG_COLORS = [PURPLE, (255, 0, 255), (0, 255, 255), (100, 50, 0), (100, 200, 150), (50, 100, 200)]
LOG_FILE = "log_trab5.csv" 
MODO_ESCOLHIDO, all_agents, num_agents_procedural = None, [], 5
LOG = [] 

# classe que define comportamento de cada agente
class Agente:
    def __init__(self, start, end, color, single_mode=False):
        self.start, self.end, self.current_spot, self.color = start, end, start, color
        self.path, self.path_index, self.running, self.single_mode = [], 0, False, single_mode
        
    def find_path(self, grid):
        result, came_from = algorithm(lambda: draw(WIN, grid, ROWS, WIDTH), grid, self.start, self.end, True)
        if result:
            path_list = []; current = self.end
            while current in came_from:
                current = came_from[current]; path_list.append(current)
            path_list.pop()
            self.path = path_list; self.path_index = len(self.path) - 1
            self.running = True
            self.start.make_start(self.color); self.end.make_end(self.color)
            return True
        return False

    def move(self):
        if self.running and self.path_index > 0:
            if self.current_spot != self.start and self.current_spot != self.end: 
                self.current_spot.make_path(BLACK)
            self.path_index -= 1
            self.current_spot = self.path[self.path_index]
            self.current_spot.make_agent_pos(self.color)
            return True
        elif self.running and self.path_index == 0:
            if self.current_spot != self.start and self.current_spot != self.end: self.current_spot.make_path(BLACK)
            self.current_spot = self.end
            self.running = False
            return False
        return False

# classe que define cada célula (quadradinho)
class Celula:
    def __init__(self, r, c, w, tr):
        self.row, self.col, self.width, self.total_rows = r, c, w, tr
        self.x, self.y, self.color, self.original_color = r * w, c * w, WHITE, WHITE
        self.neighbors, self.is_agent, self.agent_color = [], False, None
    def get_pos(self): return self.row, self.col
    def is_start(self): return self.color == BLUE
    def is_end(self): return self.color == YELLOW
    def is_barrier(self): return self.color == BLACK
    def make_start(self, color): self.color = self.original_color = color
    def make_end(self, color): self.color = self.original_color = color
    def make_barrier(self): self.color = self.original_color = BLACK
    def make_closed(self): 
        if self.original_color == WHITE: self.color = RED
    def make_open(self): 
        if self.original_color == WHITE: self.color = GREEN
    def make_path(self, color): 
        if self.original_color == WHITE: self.color = color
    def make_agent_pos(self, color): 
        self.is_agent, self.agent_color, self.color = True, color, color
    def reset(self): 
        self.color = self.original_color = WHITE; self.is_agent = False
    
    def draw(self, win):
        if self.is_agent:
            pygame.draw.circle(win, self.agent_color, (self.x + self.width // 2, self.y + self.width // 2), self.width // 2 - 2)
        else:
            pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))
    
    def update_neighbors(self, grid):
        self.neighbors = []
        R, C, max_r = self.row, self.col, self.total_rows
        if R < max_r - 1 and not grid[R + 1][C].is_barrier(): self.neighbors.append(grid[R + 1][C])
        if R > 0 and not grid[R - 1][C].is_barrier(): self.neighbors.append(grid[R - 1][C])
        if C < max_r - 1 and not grid[R][C + 1].is_barrier(): self.neighbors.append(grid[R][C + 1])
        if C > 0 and not grid[R][C - 1].is_barrier(): self.neighbors.append(grid[R][C - 1])
    def __lt__(self, other): return False

# funções A*
def h(p1, p2):
    x1, y1 = p1; x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)

def algorithm(draw, grid, start, end, single_agent_run=False):
    count = 0; open_set = PriorityQueue(); open_set.put((0, count, start))
    came_from, g_score, f_score = {}, {s: float("inf") for r in grid for s in r}, {s: float("inf") for r in grid for s in r}
    g_score[start], f_score[start] = 0, h(start.get_pos(), end.get_pos()); open_set_hash = {start}

    while not open_set.empty():
        if not single_agent_run:
             for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    pygame.quit(); 
                    sys.exit()

        current = open_set.get()[2]
        open_set_hash.remove(current)
        if current == end: return True, came_from 
        for neighbor in current.neighbors:
            temp_g_score = g_score[current] + 1
            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current; g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + h(neighbor.get_pos(), end.get_pos())
                if neighbor not in open_set_hash:
                    count += 1; open_set.put((f_score[neighbor], count, neighbor)); open_set_hash.add(neighbor)
                    if not neighbor.is_agent and not neighbor.is_end() and not neighbor.is_start(): neighbor.make_open()
        if not single_agent_run: draw()
        if current != start and current != end and not current.is_agent: current.make_closed()
    return False, {}

def make_grid(rows, width):
    grid, gap = [], width // rows
    for i in range(rows):
        grid.append([])
        for j in range(rows): grid[i].append(Celula(i, j, gap, rows))
    return grid

def draw_grid(win, rows, width):
    gap = width // rows
    for i in range(rows):
        pygame.draw.line(win, BLACK, (0, i * gap), (width, i * gap))
        pygame.draw.line(win, BLACK, (i * gap, 0), (i * gap, width))

def draw(win, grid, rows, width):
    win.fill(WHITE)
    for row in grid:
        for spot in row: spot.draw(win)
    draw_grid(win, rows, width)
    
    text_info = "Pressione 'C' para limpar"
    if MODO_ESCOLHIDO == '1':
        text_info = "Modo interativo Mouse: Origem/Destino/Barreiras | Espaço: 1 Agente | G: Mais agentes| C: Limpar"
    elif MODO_ESCOLHIDO == '2':
        text_info = "Modo procedural: | C: Limpar"

    text_surface = FONT.render(text_info, True, BLACK)
    pygame.draw.rect(win, GREEN, (0, width, width, 30))
    win.blit(text_surface, (10, width + 5))
    pygame.display.update()

def get_clicked_pos(pos, rows, width):
    gap = width // rows; y, x = pos
    return y // gap, x // gap

def get_random_pos(grid):
    num_rows = len(grid); num_cols = len(grid[0])
    r = random.randint(0, num_rows - 1)
    c = random.randint(0, num_cols - 1)
    return grid[r][c]

# função para salvar log
def save_session_log(log_data):
    if not log_data: return
    try:
        file_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists or os.path.getsize(LOG_FILE) == 0:
                writer.writerow(["Timestamp", "Modo", "Acao", "Detalhes"])
            writer.writerows(log_data)
        print(f"\nLog de sessão salvo")
    except Exception as e:
        print(f"Erro ao salvar o log: {e}")

def generate_random_agents(grid, num_agents):
    agents, colors = [], random.sample(AG_COLORS, min(num_agents, len(AG_COLORS)))
    used_start, used_end = set(), set()
    
    for i in range(num_agents):
        color = colors[i % len(colors)]
        while True:
            start, end = get_random_pos(grid), get_random_pos(grid)
            if (not start.is_barrier() and not end.is_barrier() and start != end and
                start not in used_start and end not in used_end):
                used_start.add(start); used_end.add(end)
                start.reset(); end.reset()
                agents.append(Agente(start, end, color)); break
    for agent in agents:
        for row in grid:
            for spot in row: spot.update_neighbors(grid)
        agent.find_path(grid)
        for row in grid:
            for spot in row:
                if spot.color in [RED, GREEN]: spot.reset() 
        agent.start.make_start(agent.color)
        agent.end.make_end(agent.color)
    return agents

# funções de input e modo
def get_user_input(win, width, prompt):
    FONT_INPUT = pygame.font.Font(None, 36)
    input_box = pygame.Rect(width // 2 - 50, width // 2, 140, 32)
    text = '5'
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try: num = int(text); return num if num > 0 else 1
                    except ValueError: text = '5'
                elif event.key == pygame.K_BACKSPACE: text = text[:-1]
                elif event.unicode.isdigit() and len(text) < 3: text += event.unicode
        
        win.fill(WHITE)
        prompt_surf = FONT_INPUT.render(prompt, True, BLACK)
        win.blit(prompt_surf, (width // 2 - prompt_surf.get_width() // 2, width // 2 - 60))
        
        txt_surface = FONT_INPUT.render(text, True, BLACK)
        input_box.width = max(200, txt_surface.get_width() + 10)
        win.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(win, BLACK, input_box, 2)
        pygame.display.flip()

def escolher_modo_inicial(win, width):
    FONT_MENU = pygame.font.Font(None, 36)
    c_x, c_y = width // 2, width // 2
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                save_session_log(LOG) 
                pygame.quit(); 
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return '1'
                elif event.key == pygame.K_2:
                    num_ag = get_user_input(win, width, "Número de agentes: ")
                    return ('2', num_ag)
        
        win.fill(WHITE)
        t = FONT_MENU.render("Selecione o modo de execução", True, BLACK)
        op1 = FONT_MENU.render("1: interativo", True, BLACK)
        op2 = FONT_MENU.render("2: procedural", True, BLACK)
        
        win.blit(t, (c_x - op1.get_width() // 2, c_y - 100))
        win.blit(op1, (c_x - op1.get_width() // 2, c_y))
        win.blit(op2, (c_x - op2.get_width() // 2, c_y + 50))
        pygame.display.flip()

# função de execução principal
def main(win, width):
    global MODO_ESCOLHIDO, all_agents, num_agents_procedural, ROWS
    global LOG
    
    resultado_modo = escolher_modo_inicial(win, width)
    MODO_ESCOLHIDO = resultado_modo[0] if isinstance(resultado_modo, tuple) else resultado_modo
    if isinstance(resultado_modo, tuple): num_agents_procedural = resultado_modo[1]
    
    modo_str = "Interativo" if MODO_ESCOLHIDO == '1' else f"Procedural ({num_agents_procedural} Ags)"
    LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), modo_str, "INICIO_SESSAO", f"Res={ROWS}"])

    grid, start_cell, end_cell, running = make_grid(ROWS, width), None, None, False
    
    if MODO_ESCOLHIDO == '2':
        for _ in range(300): get_random_pos(grid).make_barrier()
        all_agents = generate_random_agents(grid, num_agents_procedural)
        running = True
        LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), modo_str, "GERAR_PROCEDURAL", f"{num_agents_procedural} agentes"])
        
    while True:
        draw(win, grid, ROWS, width) 
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                save_session_log(LOG)
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                start_cell, end_cell, all_agents, running, grid = None, None, [], False, make_grid(ROWS, width)
                LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), MODO_ESCOLHIDO, "LIMPAR_GRID", "C"])
                if MODO_ESCOLHIDO == '2':
                    for _ in range(300): get_random_pos(grid).make_barrier()
                    all_agents = generate_random_agents(grid, num_agents_procedural)
                    running = True
            if MODO_ESCOLHIDO == '1' and not running:
                if pygame.mouse.get_pressed()[0] and pygame.mouse.get_pos()[1] < WIDTH: # log de cliques
                    r, c = get_clicked_pos(pygame.mouse.get_pos(), ROWS, width); cell = grid[r][c]    
                    acao = "Barreira"
                    if not start_cell and not cell.is_end(): start_cell = cell; start_cell.make_start(BLUE); acao = "Start"
                    elif not end_cell and not cell.is_start(): end_cell = cell; end_cell.make_end(YELLOW); acao = "End"
                    elif not cell.is_end() and not cell.is_start(): cell.make_barrier()
                    LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), MODO_ESCOLHIDO, f"CLIQUE_ESQUERDO", f"{acao} @({r},{c})"])
                elif pygame.mouse.get_pressed()[2] and pygame.mouse.get_pos()[1] < WIDTH:
                    r, c = get_clicked_pos(pygame.mouse.get_pos(), ROWS, width); cell = grid[r][c]
                    if cell.color != WHITE:
                        LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), MODO_ESCOLHIDO, "CLIQUE_DIREITO", f"Remover @({r},{c})"])
                    cell.reset()
                    if cell == start_cell: start_cell = None
                    elif cell == end_cell: end_cell = None
                # espaço: 1 agente
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and start_cell and end_cell:
                    for r_ in grid:
                        for s_ in r_:
                            if s_.color not in [BLACK, BLUE, PURPLE]: s_.reset()
                    single_agent = Agente(start_cell, end_cell, PURPLE, True); all_agents = [single_agent] 
                    for r_ in grid:
                        for s_ in r_: s_.update_neighbors(grid)
                    if single_agent.find_path(grid): running = True
                    LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), MODO_ESCOLHIDO, "RUN_1_AGENTE", f"Start:({start_cell.row},{start_cell.col})"])
                # G: múltiplos agentes
                if event.type == pygame.KEYDOWN and event.key == pygame.K_g: 
                    for r_ in grid:
                        for s_ in r_:
                            if s_.color not in [BLACK]: s_.reset()
                    start_cell, end_cell = None, None
                    num_agentes_interativo = get_user_input(win, width, "Número de agentes: (Enter)")
                    all_agents = generate_random_agents(grid, num_agentes_interativo)
                    running = True
                    LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), MODO_ESCOLHIDO, "RUN_MULTI_AGENTE", f"{num_agentes_interativo} agentes"])      
        if running and all_agents:
            all_finished = True
            for agent in all_agents:
                if agent.running: agent.move(); all_finished = False
            if all_finished: 
                running = False
                LOG.append([time.strftime("%Y-%m-%d %H:%M:%S"), MODO_ESCOLHIDO, "FIM_MOVIMENTO", f"{len(all_agents)} agentes"]) 

main(WIN, WIDTH)