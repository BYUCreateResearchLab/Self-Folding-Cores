import math

class GCodeWriter:
    def __init__(self, feed_rate=1000, power=100.0):
        self.feed_rate = feed_rate
        # Map 0-100% power to Q0-Q255
        q_val = max(0, min(255, int(power * 2.55)))
        self.power_cmd = f"M10 Q{q_val} (fire on)"
        
        self.preamble = []
        self.preamble.append("(LightBurn Core 2.0.05)")
        self.preamble.append("(Custom GCode device profile, absolute coords)")
        self.preamble.append("")
        self.preamble.append("(USER START SCRIPT)")
        self.preamble.append("G4 P5000 (wait to walk to window)")
        self.preamble.append("")
        self.preamble.append("(USER START SCRIPT)")
        self.preamble.append("G00 G17 G40 G21(Restore metric mode)")
        self.preamble.append("G54")
        self.preamble.append("G90(Restore absolute mode)")
        self.preamble.append(f"(Cut @ {self.feed_rate} mm/min, {power}% power)")
        self.preamble.append("(air off)")
        self.preamble.append("M11 (tool off)")
        
        self.layer_commands = []
        self.paths = []

    def set_layer(self, layer_name):
        self.layer_commands.append(f"({layer_name})")
        self.layer_commands.append("M3 (tool on)")

    def add_line(self, p1, p2):
        self.paths.append([p1, p2])

    def add_polygon(self, points):
        if not points: return
        closed_path = list(points) + [points[0]]
        self.paths.append(closed_path)

    def optimize_paths(self):
        if not self.paths:
            return []
            
        optimized = []
        unvisited = list(self.paths)
        
        # Start at origin
        current_point = (0.0, 0.0)
        
        while unvisited:
            best_idx = -1
            best_dist = float('inf')
            reverse_best = False
            
            for i, path in enumerate(unvisited):
                # distance to start of path
                d_start = math.hypot(path[0][0] - current_point[0], path[0][1] - current_point[1])
                # distance to end of path (if we reverse it)
                d_end = math.hypot(path[-1][0] - current_point[0], path[-1][1] - current_point[1])
                
                if d_start < best_dist:
                    best_dist = d_start
                    best_idx = i
                    reverse_best = False
                
                if d_end < best_dist:
                    best_dist = d_end
                    best_idx = i
                    reverse_best = True
                    
            chosen_path = unvisited.pop(best_idx)
            if reverse_best:
                chosen_path = list(reversed(chosen_path))
                
            optimized.append(chosen_path)
            current_point = chosen_path[-1]
            
        return optimized

    def get_gcode(self):
        lines = list(self.preamble)
        lines.extend(self.layer_commands)
        
        optimized_paths = self.optimize_paths()
        
        for path in optimized_paths:
            lines.append(f"G0 X{path[0][0]:.3f} Y{path[0][1]:.3f}")
            lines.append("M3 (tool on)")
            lines.append(f"G1 X{path[1][0]:.3f} Y{path[1][1]:.3f} F{self.feed_rate} {self.power_cmd}")
            
            for p in path[2:]:
                lines.append(f"G1 X{p[0]:.3f} Y{p[1]:.3f} {self.power_cmd}")
                
            lines.append("M11 (tool off)")

        gcode = "\n".join(lines)
        gcode += "\n(air off)\n"
        gcode += "M11 (tool off)\n"
        gcode += "G90(Restore absolute mode)\n"
        gcode += "M30\n"
        gcode += "M2\n"
        gcode += "G0 X0 Y0 Z100\n"
        return gcode


