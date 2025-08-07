from django.core.management.base import BaseCommand

from ...models import Category, Similarity


class Command(BaseCommand):
    help = ("Analyze similarity graph: show longest rabbit "
            "hole and rabbit islands")
    adjacency_dict = {}
    mode = None

    def add_arguments(self, parser):
        parser.add_argument(
            '-m', '--mode',
            choices=['fast', 'full'],
            default='full',
            help="Choose 'fast' for a fast but not proven analysis or "
                 "'full' for exhaustive (default: full)"
        )

    def handle(self, *args, **options):
        self.mode = options['mode']
        for s in Similarity.objects.all():
            self.adjacency_dict.setdefault(s.category_a_id, set()).add(
                s.category_b_id)
            self.adjacency_dict.setdefault(s.category_b_id, set()).add(
                s.category_a_id)

        categories_by_id = {c.id: c for c in Category.objects.all()}
        islands = self.collect_islands(categories_by_id)
        longest_path = self.get_longest_path(islands)

        for island in islands:
            path = self.double_bfs_diameter(island)
            if len(path) > len(longest_path):
                longest_path = path

        self.stdout.write("\nLongest rabbit hole:")
        if longest_path:
            names = [categories_by_id[i].name for i in longest_path]
            self.stdout.write(" -> ".join(names))
        else:
            self.stdout.write("None found.")

        self.stdout.write("\nRabbit Islands:")
        for i, island in enumerate(islands, 1):
            self.stdout.write(
                f"Island {i}: {[categories_by_id[i].name for i in island]}")

    def collect_island(self, start):
        island = set()
        queue = [start]
        while queue:
            node = queue.pop()
            if node not in island:
                island.add(node)
                queue.extend(self.adjacency_dict.get(node, []))
        return island

    def collect_islands(self, categories_by_id):
        visited = set()
        islands = []

        for cat_id in categories_by_id:
            if cat_id not in visited:
                island = self.collect_island(cat_id)
                visited.update(island)
                islands.append(island)

        return islands

    # Decided I'm going to have some "fun" with this so added a toggle.
    # Omitting it, or using full will calculate full bsf paths. If fast is
    # used though we get into the fun stuff. Did some digging and wanted to
    # find a way to calculate the longest rabit hole faster. I find the
    # solution a bit iffy, because I can't prove that it works up to a graph
    # with X edges, however I have not found a data set which yields different
    # results(disproving it) than the slow approach(in length at least,
    # because they may and do find different maximum rabbit holes if
    # there are multiple). The magic number 10(in double_bfs_diameter) is bad,
    # in theory it should be possible to calculate based on the amount
    # of edges and vertices what the actual number should be, but that
    # complexity is not for here.
    def get_longest_path(self, islands):
        assert self.mode in ['full', 'fast'], 'invalid mode'
        longest_path = []
        for island in islands:
            path = []
            if self.mode == 'full':
                path = self.find_longest_shortest_path(island)
            if self.mode == 'fast':
                path = self.double_bfs_diameter(island)
            if len(path) > len(longest_path):
                longest_path = path
        return longest_path

    # Simple full bfs solution
    def find_longest_shortest_path(self, island):
        max_path = []
        for node in island:
            path = self.bfs_longest_path_from(node)
            if len(path) > len(max_path):
                max_path = path
        return max_path

    def bfs_longest_path_from(self, start):
        seen = {start}
        queue = [(start, [start])]
        longest_path = []

        while queue:
            node, path = queue.pop(0)
            if len(path) > len(longest_path):
                longest_path = path

            for neighbor in self.adjacency_dict.get(node, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return longest_path

    # Fast modified bfs solution
    # This one is evil...
    # A standard BFS from every edge is too slow.
    # A normal double BFS, although half the internet says works for an
    # unweighted, simple, connected graph, which this is, I have an example
    # of it not working: we have the edges [A, B, C, D, E, F, G],
    # we define our vertices as [(A, E), (B, F), (C, G), (E, F), (F, G),
    # (D, E), (D, G)], then if we pick B or F for our first vertex, we will
    # get A, D, C, or if we pick D - B as our furthest vertices.
    # Because in a standard double BFS we pick one of them and do a second
    # BFS with it and say that we are done we have a 1/3(respectfully 1/1) in
    # each of those situations to get a smaller than the largest shortest
    # path(diameter), which because those first nodes are seven is 5/21, or an
    # almost 25% chance of a wrong result.
    # Started thinking about dijkstra, however it's complexity grows a lot:
    # Dijkstra's algorithm has a time complexity of O(|V| log |V| + |E|)
    # if implemented using Fibonacci-heaps, while BFS has a time complexity
    # of O(|V| + |E|).
    # So what I decided to do is a bit iffy, as in theory I should be able
    # to break it, but it seems to be working and I do not seem to find
    # an edge case for it not working.
    def double_bfs_diameter(self, island):
        start = next(iter(island))
        distances, _ = self.bfs_all_paths(start)
        max_dist = max(distances.values())
        farthest_nodes = [node for node, dist in distances.items() if
                          dist == max_dist]
        longest_path = []
        # Limit farthest_nodes to 10
        if len(farthest_nodes) > 10:
            farthest_nodes = farthest_nodes[:10]
        for node in farthest_nodes:
            _, paths = self.bfs_all_paths(node)
            for path in paths.values():
                if len(path) > len(longest_path):
                    longest_path = path
        return longest_path

    def bfs_all_paths(self, start):
        seen = {start}
        queue = [(start, [start])]
        distances = {start: 0}
        paths = {start: [start]}

        while queue:
            node, path = queue.pop(0)

            for neighbor in self.adjacency_dict.get(node, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    distances[neighbor] = distances[node] + 1
                    paths[neighbor] = path + [neighbor]
                    queue.append((neighbor, path + [neighbor]))
        return distances, paths
