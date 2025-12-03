# checkpoint 3
from collections import deque

def bfs_pathfind(current_map, start, goal, is_blocked):
    if start == goal:
        return [start]

    queue = deque([start])
    came_from = {start: None}

    while queue:
        cx, cy = queue.popleft()

        for nx, ny in ((cx+1,cy), (cx-1,cy), (cx,cy+1), (cx,cy-1)):
            if (nx, ny) not in came_from and not is_blocked(nx, ny):
                came_from[(nx, ny)] = (cx, cy)
                queue.append((nx, ny))

                if (nx, ny) == goal:
                    path = [(nx, ny)]
                    while path[-1] != start:
                        path.append(came_from[path[-1]])
                    path.reverse()
                    return path

    return None  # no path found
