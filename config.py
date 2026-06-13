# --- Map ---
CELL_SIZE = 32          # pixel size of each grid cell
MAP_ROWS = 30
MAP_COLS = 40

# --- Simulation ---
FPS = 30
VEHICLE_MOVE_INTERVAL = 0.3   # seconds between each step a vehicle moves
AUTO_SPAWN_INTERVAL = 5.0     # seconds between auto-spawned vehicles

# --- Traffic ---
WAIT_THRESHOLD = 5.0              # seconds before a vehicle is considered stuck
MIN_WAITING_VEHICLES = 3          # vehicles near intersection to trigger congestion
INTERSECTION_CONGESTION_TIME = 10.0  # seconds total wait at intersection to trigger reroute
REROUTE_WAIT_THRESHOLD = 10.0     # seconds before forcing reroute
MANUAL_ENFORCE_THRESHOLD = 8.0    # seconds before guard takes over a manual vehicle on road

# --- Scoring ---
CONGESTION_PENALTY = 5.0
OBSTACLE_PENALTY = 3.0

# --- Priority ---
WAIT_TIME_WEIGHT = 10
DIRECTION_BONUS_STRAIGHT = 5
DIRECTION_BONUS_TURN = 0

# --- UI ---
WINDOW_TITLE = "Smart Parking Simulation"
LOG_MAX_LINES = 20
SIDEBAR_WIDTH = 320
MAX_TOPDOWN_CAR_VARIANTS = 64
