import pygame, sys, random, time, csv, os
from queue import PriorityQueue
from datetime import datetime

WIDTH, ROWS = 700, 50 
pygame.init(); pygame.font.init() 
WIN = pygame.display.set_mode((WIDTH, WIDTH + 30))
pygame.display.set_caption("Navegação")
FONT = pygame.font.Font(None, 24)

RED, GREEN, BLUE, YELLOW, WHITE, BLACK, PURPLE = (255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,255,255), (0,0,0), (128,0,128)
AG_COLORS = [PURPLE, (255, 0, 255), (0, 255, 255), (100, 50, 0), (100, 200, 150), (50, 100, 200)]
MODO_ESCOLHIDO, num_agents_procedural = None, 5
ALGORITHM_CHOICE = 'ASTAR' 
GRID_GEOMETRY = None 

# passa pra execução sequencial
class Agente: pass

def get_base_agent(decorated_object):
    current_component = decorated_object
    while not isinstance(current_component, Agente):
        if hasattr(current_component, '_component'):
            current_component = current_component._component
        else:
            return decorated_object
    return current_component

# função para salvar log da sessão, analisar depois com colab
def save_log(agent_color, algorithm, geometry, path_len, nodes_explored, time_ms):
    filename = 'log_trab10.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['timestamp', 'cor_agente', 'algoritmo', 'geometria', 'tamanho_caminho', 'nos_explorados', 'tempo_execucao'])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            agent_color,
            algorithm, 
            geometry,
            path_len,
            nodes_explored,
            round(time_ms, 4)
        ])

# observer => interfaces
class Observer:
    def update(self, subject):
        raise NotImplementedError

class Subject:
    def __init__(self):
        self._observers = []

    # adiciona um observador
    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    # remove um observador
    def detach(self, observer: Observer):
        self._observers.remove(observer)

    # notifica todos os observadores sobre uma mudança de estado
    def notify(self):
        for observer in self._observers:
            observer.update(self)

# singleton =>  gerenciador de execução
class ExecutionManager(Observer):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ExecutionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, win, width):
        if self._initialized: return
        self.win = win
        self.width = width
        self.rows = ROWS
        self.running = False
        self.all_agents = []
        self.start_cell = None
        self.end_cell = None
        
        # self factory
        self.random_agent_factory = RandomAgenteFactory()
        self.manual_agent_factory = ManualAgentFactory()
        self.astar_factory = AStarFactory()
        self.dfs_factory = DFSFactory()
        self.dijkstra_factory = DijkstraFactory()
        
        self.grid = None 
        
        # self command => fila e histórico
        self.scheduled_commands = [] 
        self.executed_commands_history = []
        self._initialized = True

    def reset_state(self):
        global GRID_GEOMETRY
        self.start_cell = self.end_cell = None
        self.all_agents, self.running = [], False
        self.grid = make_grid(self.rows, self.width, GRID_GEOMETRY)
        self.scheduled_commands, self.executed_commands_history = [], []

        if MODO_ESCOLHIDO == '2':
            for _ in range(300): get_random_pos(self.grid).make_barrier()
            for row in self.grid:
                for spot in row: spot.update_neighbors(self.grid)
            
            factories = {'ASTAR': self.astar_factory, 'DFS': self.dfs_factory, 'DIJKSTRA': self.dijkstra_factory}
            self.all_agents = generate_random_agents(self.grid, num_agents_procedural, self.random_agent_factory, factories[ALGORITHM_CHOICE])
            if self.all_agents:
                self.schedule_move_commands() 
                self.running = True

    def schedule_move_commands(self):
        self.scheduled_commands, self.executed_commands_history = [], []
        current_time = pygame.time.get_ticks()
        time_step = 60
        reservation_table = {}

        temp_agents = [get_base_agent(a) for a in self.all_agents]
        for agent in temp_agents:
            agent.path_index = len(agent.path) - 1
            agent.current_spot = agent.start
            agent.active = True

        step_idx = 0
        while any(a.active for a in temp_agents) and step_idx < 2000:
            step_idx += 1
            for agent in temp_agents:
                if not agent.active: continue

                # define próximo destino que pretende seguir
                if agent.path_index < 0:
                    next_target = agent.end
                else:
                    next_target = agent.path[agent.path_index]

                # checagem de colisão
                if (step_idx, next_target) in reservation_table:
                    # espera tempo aleatório
                    wait_duration = random.randint(1, 3)
                    for i in range(wait_duration):
                        reservation_table[(step_idx + i, agent.current_spot)] = agent.color
                        self.scheduled_commands.append((current_time + (step_idx + i) * time_step, WaitCommand(agent, agent.current_spot)))
                    # pula o turno de movimento para esse agente
                    continue

                # reserva e move
                reservation_table[(step_idx, next_target)] = agent.color
                self.scheduled_commands.append((current_time + step_idx * time_step, MoveAgentCommand(agent, next_target, agent.current_spot)))
                agent.current_spot = next_target
                agent.path_index -= 1
                if agent.current_spot == agent.end: agent.active = False

        self.scheduled_commands.sort(key=lambda x: x[0])

    def execute_scheduled_commands(self):
        now = pygame.time.get_ticks()
        while self.scheduled_commands and self.scheduled_commands[0][0] <= now:
            _, cmd = self.scheduled_commands.pop(0)
            if cmd.execute(): self.executed_commands_history.append(cmd)
        if not self.scheduled_commands: self.running = False
        
    def set_grid(self, geometry_choice):
        global GRID_GEOMETRY
        GRID_GEOMETRY = geometry_choice
        self.grid = make_grid(self.rows, self.width, GRID_GEOMETRY)

# chain of responsability => inicialização sequencial
class ConfiguracaoHandler:
    def __init__(self, next_handler=None):
        self._next_handler = next_handler

    def set_next(self, handler):
        self._next_handler = handler
        return handler

    def handle_request(self, win, width, manager):
        result = self._process(win, width, manager)
        if result and self._next_handler:
            return self._next_handler.handle_request(win, width, manager)
        return result

    def _process(self, win, width, manager):
        raise NotImplementedError

class GeometriaHandler(ConfiguracaoHandler):
    def _process(self, win, width, manager):
        global GRID_GEOMETRY
        geometria_escolhida = escolher_geometria(win, width)
        GRID_GEOMETRY = geometria_escolhida
        manager.set_grid(GRID_GEOMETRY)
        print(f"Configuração: geometria {GRID_GEOMETRY} selecionada.")
        return True

class ModoHandler(ConfiguracaoHandler):
    def _process(self, win, width, manager):
        global MODO_ESCOLHIDO, num_agents_procedural
        resultado_modo = escolher_modo_inicial(win, width)
        MODO_ESCOLHIDO = resultado_modo[0] if isinstance(resultado_modo, tuple) else resultado_modo
        if isinstance(resultado_modo, tuple):
            num_agents_procedural = resultado_modo[1]
        manager.reset_state()
        
        print(f"Modo {MODO_ESCOLHIDO} selecionado (agentes: {num_agents_procedural}).")
        return True

# command => movimentação e desfazer
class AgentCommand:
    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

class MoveAgentCommand(AgentCommand):
    def __init__(self, agent, next_spot, prev_spot):
        self.agent = agent
        self.next_spot = next_spot
        self.prev_spot = prev_spot
        
    def execute(self):
        if self.prev_spot != self.agent.start and self.prev_spot != self.agent.end:
            self.prev_spot.make_path(BLACK)
        else:
            self.prev_spot.is_agent = False
            self.prev_spot.agent_color = None
            self.prev_spot.color = self.prev_spot.original_color 
            
        self.agent.current_spot = self.next_spot
        self.next_spot.make_agent_pos(self.agent.color)
        return True

    def undo(self):
        self.next_spot.reset()
        self.agent.current_spot = self.prev_spot
        return True

class WaitCommand(AgentCommand):
    def __init__(self, agent, spot):
        self.agent = agent
        self.spot = spot

    def execute(self):
        self.agent.current_spot = self.spot
        self.spot.make_agent_pos(self.agent.color)
        return True

    def undo(self): return True

# adapter => geometria do grid
class NeighborFinderTarget:
    def get_neighbors(self, cell, grid):
        raise NotImplementedError

class RectangularNeighborFinder(NeighborFinderTarget):
    def get_neighbors(self, cell, grid):
        neighbors = []
        R, C, max_r = cell.row, cell.col, cell.total_rows
        if R < max_r - 1 and not grid[R + 1][C].is_barrier(): neighbors.append(grid[R + 1][C])
        if R > 0 and not grid[R - 1][C].is_barrier(): neighbors.append(grid[R - 1][C])
        if C < max_r - 1 and not grid[R][C + 1].is_barrier(): neighbors.append(grid[R][C + 1])
        if C > 0 and not grid[R][C - 1].is_barrier(): neighbors.append(grid[R][C - 1])
        return neighbors

class HexagonalNeighborFinder(NeighborFinderTarget):
    HEX_DIRECTIONS_EVEN = [(0, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)] 
    HEX_DIRECTIONS_ODD = [(0, 1), (1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1)] 

    def get_neighbors(self, cell, grid):
        neighbors = []
        R, C, max_r = cell.row, cell.col, cell.total_rows
        is_odd = R % 2 != 0
        directions = self.HEX_DIRECTIONS_ODD if is_odd else self.HEX_DIRECTIONS_EVEN
        for d_r, d_c in directions:
            new_r, new_c = R + d_r, C + d_c
            if 0 <= new_r < max_r and 0 <= new_c < max_r:
                neighbor = grid[new_r][new_c]
                if not neighbor.is_barrier():
                    neighbors.append(neighbor)
        return neighbors

# decorator => algoritmo de busca dijkstra
class SearchComponent:
    def find_path(self, grid):
        raise NotImplementedError

class SearchDecorator(SearchComponent):
    def __init__(self, component: SearchComponent):
        self._component = component
    def find_path(self, grid):
        return self._component.find_path(grid)

class DijkstraSearchDecorator(SearchDecorator):
    def find_path(self, grid):
        base_agent = get_base_agent(self)
        original_factory = base_agent.algorithm_factory
        dijkstra_factory = DijkstraFactory()
        base_agent.algorithm_factory = dijkstra_factory
        result = self._component.find_path(grid)
        base_agent.algorithm_factory = original_factory
        return result

# classe que define comportamento de cada agente
class Celula:
    def __init__(self, r, c, w, tr, neighbor_finder):
        self.row, self.col, self.width, self.total_rows = r, c, w, tr
        self.color, self.original_color = WHITE, WHITE
        self.neighbors, self.is_agent, self.agent_color = [], False, None
        self._neighbor_finder = neighbor_finder 
        
        self.hex_R = self.width / 2.0  
        self.hex_H = self.hex_R * 0.866025404 

        self.x, self.y = c * w, r * w

    def get_pos(self): return self.row, self.col
    def is_start(self): return self.color in [BLUE] + AG_COLORS 
    def is_end(self): return self.color in [YELLOW] + AG_COLORS 
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
        self.color = self.original_color = WHITE; self.is_agent = False; self.agent_color = None
    
    def _get_hex_points(self, center_x, center_y):
        points = []
        for i in range(6):
            angle_deg = 60 * i + 30 
            x = center_x + self.hex_R * pygame.math.Vector2(1, 0).rotate(-angle_deg).x
            y = center_y + self.hex_R * pygame.math.Vector2(1, 0).rotate(-angle_deg).y
            points.append((x, y))
        return points
    
    def get_center_coords(self):
        hex_R, hex_H = self.hex_R, self.hex_H
        hex_width = hex_R * 2
        center_x = (self.col * hex_width * 0.75) + hex_R
        center_y = (self.row * hex_H * 1.5) + hex_H 
        if self.row % 2 != 0:
            center_x += hex_width * 0.375 
        return center_x, center_y

    def draw(self, win):
        global GRID_GEOMETRY
        
        center_x, center_y = self.get_center_coords()
        agent_pos = (center_x, center_y)
        
        if GRID_GEOMETRY == 'HEXAGONAL':
            points = self._get_hex_points(center_x, center_y)
            pygame.draw.polygon(win, self.color, points)
            pygame.draw.polygon(win, BLACK, points, 1)
        else:
            self.x, self.y = self.col * self.width, self.row * self.width
            pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))
            agent_pos = (self.x + self.width // 2, self.y + self.width // 2)
        if self.is_agent:
            pygame.draw.circle(win, self.agent_color, agent_pos, int(self.width / 2) - 2)
            
            if MODO_ESCOLHIDO == '2':
                 manager = ExecutionManager()
                 base_agent_in_list = False
                 for a in manager.all_agents:
                     base_a = get_base_agent(a)
                     if base_a.current_spot == self:
                         base_agent_in_list = base_a
                         break
                 if base_agent_in_list and hasattr(base_agent_in_list, 'life'):
                    FONT_LIFE = pygame.font.Font(None, 16)
                    # Usa o life do agente base, mesmo se for decorado
                    life_text = FONT_LIFE.render(str(base_agent_in_list.life), True, WHITE if self.color == BLACK else BLACK)
                    win.blit(life_text, (agent_pos[0] - life_text.get_width() // 2, agent_pos[1] - life_text.get_height() // 2))

    def update_neighbors(self, grid):
        self.neighbors = self._neighbor_finder.get_neighbors(self, grid)
    def __lt__(self, other): return False

# classe agente para trabalhar em conjunto com o decorator
class Agente(SearchComponent, Subject):
    def __init__(self, start, end, color, single_mode=False, algorithm_factory=None):
        Subject.__init__(self) 
        self.start, self.end, self.current_spot, self.color = start, end, start, color
        self.path, self.path_index, self.running, self.single_mode = [], 0, False, single_mode
        self.algorithm_factory = algorithm_factory

    def find_path(self, grid):
        algorithm_func = self.algorithm_factory.get_algorithm()

        # inicio do contador de tempo (para o csv)
        start_time = time.perf_counter()
        success, came_from, nodes_explored = algorithm_func(lambda: draw(WIN, grid, ROWS, WIDTH), grid, self.start, self.end, True)
        end_time = time.perf_counter()
        tempo_exec = (end_time - start_time) * 1000

        if success:
            path_list = []
            current = self.end
            while current in came_from and current != self.start:
                path_list.append(current)
                current = came_from[current]
            self.path = path_list
            self.path_index = len(self.path) - 1
            save_log(self.color, ALGORITHM_CHOICE, GRID_GEOMETRY, len(path_list), nodes_explored, tempo_exec)
            self.running = True
            self.start.make_start(self.color)
            self.end.make_end(self.color)
            return True
        return False
        
        if algorithm_func == AStar_algorithm or algorithm_func == dijkstra_algorithm or algorithm_func == dfs_algorithm: 
            result, came_from = algorithm_func(lambda: draw(WIN, grid, ROWS, WIDTH), grid, self.start, self.end, True)
        
        if result:
            path_list = []; current = self.end
            while current in came_from and current != self.start:
                path_list.append(current); current = came_from[current]
            if path_list and path_list[-1] == self.start: path_list.pop()
            self.path = path_list; self.path_index = len(self.path) - 1
            self.running = True
            self.start.make_start(self.color); self.end.make_end(self.color)
            return True
        return False

    def create_move_command_for_schedule(self):
        if self.running and self.path_index >= 0:
            
            # determina o próximo passo
            if self.path_index == 0:
                 next_spot = self.end
            else:
                 # usa o path_index para obter o próximo passo da rota pré-calculada
                 next_spot = self.path[self.path_index - 1]
            
            # verifica se o espaço está ocupado por outro agente
            if next_spot != self.end and next_spot.is_agent and next_spot.agent_color != self.color:
                
                # se os agentes colidirem => perde hp ou morre (0hp)
                if MODO_ESCOLHIDO == '2':
                    print(f"Agente {self.color} detectou colisão FUTURA em {next_spot.get_pos()}. Falha na criação do comando.")
                    self.take_damage() #
                    self.path_index = -1
                    self.running = False
                    return None
                else:
                    print(f"Agente {self.color} impedido de mover para {next_spot.get_pos()} (colisão preditiva).")
                    self.running = False
                    return None

            prev_spot = self.current_spot
            
            # cria o command de movimento
            move_command = MoveAgentCommand(self, next_spot, prev_spot)
            
            # atualiza o index para a próxima iteração da fila
            self.path_index -= 1
            return move_command

        self.running = False
        return None

# fábrica genérica/abstrata de agentes + fábricas focadas para cada tipo de execução
class AgenteFactory:
    def create_agent(self, **kwargs):
        algo_factory = kwargs.get('algorithm_factory')
        if not algo_factory:
             raise ValueError("algorithm_factory não foi fornecido")
        raise NotImplementedError("subclasses não implementam 'create_agent'")

class RandomAgenteFactory(AgenteFactory):
    def create_agent(self, start, end, color, **kwargs):
        algo_factory = kwargs.get('algorithm_factory')
        agent = Agente(start, end, color, single_mode=False, algorithm_factory=algo_factory)
        agent.attach(ExecutionManager())
        return agent

class ManualAgentFactory(AgenteFactory):
    def create_agent(self, start, end, color, **kwargs):
        algo_factory = kwargs.get('algorithm_factory')
        agent = Agente(start, end, color, single_mode=True, algorithm_factory=algo_factory)
        agent.attach(ExecutionManager())
        return agent

class AlgoritmoFactory:
    def get_algorithm(self):
        raise NotImplementedError("erro ao retornar a função de algoritmo")

class AStarFactory(AlgoritmoFactory):
    def get_algorithm(self):
        return AStar_algorithm

class DFSFactory(AlgoritmoFactory):
    def get_algorithm(self):
        return dfs_algorithm 

class DijkstraFactory(AlgoritmoFactory):
    def get_algorithm(self):
        return dijkstra_algorithm 

# funções de heurística e definição de algoritmos de busca
def h(cell1, cell2):
    x1, y1 = cell1.get_pos()
    x2, y2 = cell2.get_pos()
    return abs(x1 - x2) + abs(y1 - y2)

def AStar_algorithm(draw, grid, start, end, single_agent_run=False):
    count = 0; nodes_explored = 0
    open_set = PriorityQueue(); open_set.put((0, count, start))
    g_score = {s: float("inf") for r in grid for s in r}
    f_score = {s: float("inf") for r in grid for s in r}
    g_score[start], f_score[start] = 0, h(start, end) 
    came_from, open_set_hash = {}, {start}
    
    while not open_set.empty():
        current = open_set.get()[2]; open_set_hash.remove(current)
        nodes_explored += 1
        
        if current == end: return True, came_from, nodes_explored 
        
        for neighbor in current.neighbors:
            temp_g_score = g_score[current] + 1
            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current; g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + h(neighbor, end) 
                if neighbor not in open_set_hash:
                    count += 1; open_set.put((f_score[neighbor], count, neighbor)); open_set_hash.add(neighbor)
                    if not neighbor.is_barrier() and not neighbor.is_end() and not neighbor.is_start(): neighbor.make_open()
        if not single_agent_run: draw()
    return False, {}, nodes_explored

def dijkstra_algorithm(draw, grid, start, end, single_agent_run=False):
    count = 0; nodes_explored = 0
    open_set = PriorityQueue(); open_set.put((0, count, start))
    came_from, g_score = {}, {s: float("inf") for r in grid for s in r}
    g_score[start] = 0; open_set_hash = {start}
    
    while not open_set.empty():
        current = open_set.get()[2]; open_set_hash.remove(current)
        nodes_explored += 1
        
        if current == end: return True, came_from, nodes_explored 
        
        for neighbor in current.neighbors:
            temp_g_score = g_score[current] + 1
            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current; g_score[neighbor] = temp_g_score
                if neighbor not in open_set_hash:
                    count += 1; open_set.put((temp_g_score, count, neighbor)); open_set_hash.add(neighbor)
                    if not neighbor.is_barrier() and not neighbor.is_end() and not neighbor.is_start(): neighbor.make_open()
        if not single_agent_run: draw()
    return False, {}, nodes_explored

def dfs_algorithm(draw, grid, start, end, single_agent_run=False):
    stack, visited, came_from = [start], {start}, {}; nodes_explored = 0
    while stack:
        current = stack.pop(); nodes_explored += 1
        if current == end: return True, came_from, nodes_explored 
        for neighbor in reversed(current.neighbors): 
            if neighbor not in visited:
                visited.add(neighbor); came_from[neighbor] = current; stack.append(neighbor)
                if not neighbor.is_barrier() and not neighbor.is_end() and not neighbor.is_start(): neighbor.make_open()       
        if not single_agent_run: draw()
    return False, {}, nodes_explored

# funções de ui
def get_hex_dimensions(gap):
    R = gap / 2.0  
    H = R * 0.866025404  
    return R, H

def make_grid(rows, width, geometry_choice):
    grid = []
    if geometry_choice == 'RECTANGULAR':
        finder = RectangularNeighborFinder()
        gap = width // rows
        print("Geometria: retangular")
    elif geometry_choice == 'HEXAGONAL':
        finder = HexagonalNeighborFinder()      
        gap_total = width / (rows * 0.75 + 0.25)
        gap = int(gap_total)
        print(f"Geometria: hexagonal")
    else:
        finder = RectangularNeighborFinder()
        gap = width // rows
    for i in range(rows):
        grid.append([])
        for j in range(rows): 
            grid[i].append(Celula(i, j, gap, rows, finder))
    return grid

def draw_grid(win, rows, width):
    global GRID_GEOMETRY
    if GRID_GEOMETRY == 'RECTANGULAR':
        gap = width // rows
        for i in range(rows):
            pygame.draw.line(win, BLACK, (0, i * gap), (width, i * gap))
            pygame.draw.line(win, BLACK, (i * gap, 0), (i * gap, width))

def draw(win, grid, rows, width):
    win.fill(WHITE)
    for row in grid:
        for spot in row: spot.draw(win)
    draw_grid(win, rows, width) 
    global ALGORITHM_CHOICE, GRID_GEOMETRY
    algo_display = "A*" if ALGORITHM_CHOICE == 'ASTAR' else "DFS"
    if ALGORITHM_CHOICE == 'DIJKSTRA': algo_display = "Dijkstra"
    geo_display = "Retangular" if GRID_GEOMETRY == 'RECTANGULAR' else "Hexagonal"
    text_info = f"Algoritmo: {algo_display} | Grid: {geo_display} | A: A* | D: DFS | K: Dijkstra | C: limpar | U: desfazer"
    if MODO_ESCOLHIDO == '1':
        text_info += " | Espaço: 1 agente"
    text_surface = FONT.render(text_info, True, BLACK)
    pygame.draw.rect(win, GREEN, (0, width, width, 30))
    win.blit(text_surface, (10, width + 5))
    pygame.display.update()

def get_clicked_pos(pos, rows, width):
    gap = width // rows
    x, y = pos
    r = y // gap
    c = x // gap
    return r, c

def get_hex_clicked_pos(pos, rows, width):
    gap_total = width / (rows * 0.75 + 0.25)
    gap = int(gap_total) 
    
    R, H = get_hex_dimensions(gap)
    x, y = pos
    r = int(y / (1.5 * H))
    if r < 0 or r >= rows: return -1, -1  
    is_odd = r % 2 != 0
    adjusted_x = x
    if is_odd:
        adjusted_x -= R * 0.75 
    c = int(adjusted_x / (R * 1.5))
    if c >= rows or c < 0:
        return -1, -1
    return r, c

def get_random_pos(grid):
    num_rows = len(grid); num_cols = len(grid[0])
    r = random.randint(0, num_rows - 1)
    c = random.randint(0, num_cols - 1)
    return grid[r][c]

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
                pygame.quit(); 
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return '1'
                elif event.key == pygame.K_2:
                    num_ag = get_user_input(win, width, "Número de agentes: ")
                    return ('2', num_ag)
        
        win.fill(WHITE)
        t = FONT_MENU.render("Selecione o modo de execução", True, PURPLE)
        op1 = FONT_MENU.render("1 : Interativo", True, BLACK)
        op2 = FONT_MENU.render("2 : Procedural", True, BLACK)
        win.blit(t, (c_x - t.get_width() // 2, c_y - 100))
        win.blit(op1, (c_x - op1.get_width() // 2, c_y))
        win.blit(op2, (c_x - op2.get_width() // 2, c_y + 50))
        pygame.display.flip()

def escolher_geometria(win, width):
    FONT_MENU = pygame.font.Font(None, 36)
    c_x, c_y = width // 2, width // 2
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit(); 
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return 'RECTANGULAR'
                elif event.key == pygame.K_2: return 'HEXAGONAL'
        
        win.fill(WHITE)
        t = FONT_MENU.render("Selecione a geometria do grid", True, PURPLE)
        op1 = FONT_MENU.render("1 : Retangular", True, BLACK)
        op2 = FONT_MENU.render("2 : Hexagonal", True, BLACK)
        win.blit(t, (c_x - t.get_width() // 2, c_y - 100))
        win.blit(op1, (c_x - op1.get_width() // 2, c_y))
        win.blit(op2, (c_x - op2.get_width() // 2, c_y + 50))
        pygame.display.flip()

def generate_random_agents(grid, num_agents, factory: AgenteFactory, algorithm_factory: AlgoritmoFactory):
    agents = []; colors = AG_COLORS; used_start, used_end = set(), set(); attempts_limit = 200 
    
    # resetar todo o grid antes de gerar agentes
    for r in grid:
        for s in r: s.reset()

    while len(agents) < num_agents:
        color = colors[len(agents) % len(colors)]; start_found = False; attempts = 0
        while not start_found and attempts < attempts_limit:
            start, end = get_random_pos(grid), get_random_pos(grid)
            if (not start.is_barrier() and not end.is_barrier() and start != end and
                start not in used_start and end not in used_end):              
                
                # reseta e marca as posições
                start.reset(); end.reset()              
                used_start.add(start); used_end.add(end)
                
                agent = factory.create_agent(start, end, color, algorithm_factory=algorithm_factory)
                agents.append(agent)
                start_found = True
                break                
            attempts += 1
        if not start_found:
             print(f"Falha ao encontrar posições de origem/destino para o agente {len(agents) + 1} após {attempts_limit} tentativas")
             break   
    
    # apenas agentes com caminhos válidos são retornados
    valid_agents = []
    for agent in agents:
        if agent.find_path(grid):
            valid_agents.append(agent)
            for row in grid:
                for spot in row:
                    if spot.color in [RED, GREEN]: spot.reset()
        else:
            # se o caminho falhar, reseta as células e remove das usadas
            agent.start.reset(); agent.end.reset()
            if agent.start in used_start: used_start.remove(agent.start)
            if agent.end in used_end: used_end.remove(agent.end)
            print(f"Caminho não encontrado para agente {agent.color}!")
    
    # coloca os agentes em suas posições iniciais para visualização
    for agent in valid_agents:
        agent.start.make_agent_pos(agent.color)
        agent.end.make_end(agent.color) 

    return valid_agents

# função main
def main(win, width):
    global MODO_ESCOLHIDO, num_agents_procedural, ALGORITHM_CHOICE, GRID_GEOMETRY
    
    manager = ExecutionManager()
    manager.initialize(win, width)
    
    # chain of responsability (ordem)
    geometria_handler = GeometriaHandler()
    modo_handler = ModoHandler()
    geometria_handler.set_next(modo_handler)
    config_ok = geometria_handler.handle_request(win, width, manager)
    
    if not config_ok:
        pygame.quit()
        sys.exit()

    # loop principal
    while True:
        draw(manager.win, manager.grid, manager.rows, manager.width) 
        
        current_base_factory = manager.astar_factory
        if ALGORITHM_CHOICE == 'ASTAR':
            current_base_factory = manager.astar_factory
        elif ALGORITHM_CHOICE == 'DFS':
            current_base_factory = manager.dfs_factory
        elif ALGORITHM_CHOICE == 'DIJKSTRA':
            current_base_factory = manager.dijkstra_factory
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit(); sys.exit() 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a: ALGORITHM_CHOICE = 'ASTAR'; print("Algoritmo selecionado: A*")
                elif event.key == pygame.K_d: ALGORITHM_CHOICE = 'DFS'; print("Algoritmo selecionado: DFS")
                elif event.key == pygame.K_k: ALGORITHM_CHOICE = 'DIJKSTRA'; print("Algoritmo selecionado: Dijkstra")
                if event.key == pygame.K_c:
                    manager.reset_state()
                
                if event.key == pygame.K_u:
                    manager.undo_last_command()

                if MODO_ESCOLHIDO == '1' and not manager.running:
                    if event.key == pygame.K_SPACE and manager.start_cell and manager.end_cell:
                        for r_ in manager.grid:
                            for s_ in r_:
                                if s_.color in [RED, GREEN, BLACK] and not s_.is_barrier(): s_.reset()
                                if s_.color == PURPLE: s_.reset()
                        
                        agent = manager.manual_agent_factory.create_agent(manager.start_cell, manager.end_cell, PURPLE, algorithm_factory=current_base_factory)
                        
                        decorated_agent = agent 
                        # aplica o decorator apenas se o algoritmo escolhido for o dijkstra
                        if ALGORITHM_CHOICE == 'DIJKSTRA':
                            decorated_agent = DijkstraSearchDecorator(agent) 
                        manager.all_agents = [decorated_agent] 
                        
                        # recalcula o caminho
                        if decorated_agent.find_path(manager.grid): 
                            manager.schedule_move_commands()
                            manager.running = True
                            for r_ in manager.grid:
                                for s_ in r_:
                                    if s_.color in [RED, GREEN]: s_.reset()
                        else:
                            print("Caminho não encontrado para o agente!")
                            manager.reset_state()
                                
            if MODO_ESCOLHIDO == '1' and not manager.running:
                if pygame.mouse.get_pressed()[0] and pygame.mouse.get_pos()[1] < WIDTH: 
                    if GRID_GEOMETRY == 'HEXAGONAL':
                        r, c = get_hex_clicked_pos(pygame.mouse.get_pos(), manager.rows, manager.width)
                    else:
                        r, c = get_clicked_pos(pygame.mouse.get_pos(), manager.rows, manager.width)
                    if r != -1 and c != -1:
                        cell = manager.grid[r][c]    
                        if not manager.start_cell and not cell.is_end(): manager.start_cell = cell; manager.start_cell.make_start(BLUE)
                        elif not manager.end_cell and not cell.is_start(): manager.end_cell = cell; manager.end_cell.make_end(YELLOW)
                        elif not cell.is_end() and not cell.is_start(): cell.make_barrier()
                        
                        for row in manager.grid:
                            for spot in row: spot.update_neighbors(manager.grid)
                elif pygame.mouse.get_pressed()[2] and pygame.mouse.get_pos()[1] < WIDTH:
                    if GRID_GEOMETRY == 'HEXAGONAL':
                        r, c = get_hex_clicked_pos(pygame.mouse.get_pos(), manager.rows, manager.width)
                    else:
                        r, c = get_clicked_pos(pygame.mouse.get_pos(), manager.rows, manager.width)
                    if r != -1 and c != -1:
                        cell = manager.grid[r][c]
                        cell.reset()
                        if cell == manager.start_cell: manager.start_cell = None
                        elif cell == manager.end_cell: manager.end_cell = None
                        
                        for row in manager.grid:
                            for spot in row: spot.update_neighbors(manager.grid)

        if manager.running:
            manager.execute_scheduled_commands()

if __name__ == '__main__':
    main(WIN, WIDTH)