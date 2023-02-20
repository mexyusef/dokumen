import jpype
import jpype.imports
from pyvis.network import Network
import networkx as nx

from typing import List

from utils import extract_nx_source_name, extract_nx_target_name, file_write
from network import SourceNode, SinkNode, NodeSelector

CALLERS_FILE = 'callers.txt'
CALLEES_FILE = 'callees.txt'
CALLGRAPH_JAR_FILE = 'callgraph.jar'
CALLGRAPH_PACKAGE = 'de.fulgent.callgraph'
DEMO_SOURCE_CLASS_COLOR = []
DEMO_SINK_CLASS_COLOR = []

def populate_config(filename='source-color.txt', config='source'):
    global DEMO_SOURCE_CLASS_COLOR, DEMO_SINK_CLASS_COLOR

    with open(filename, 'r') as file:
        config_list = [tuple(line.strip().split('=')) for line in file.readlines() if line.strip() and not line.startswith('#')]
    if config == 'source':
        DEMO_SOURCE_CLASS_COLOR = [(key, value) for key, value in config_list]
    elif config == 'sink':
        DEMO_SINK_CLASS_COLOR = [(key, value) for key, value in config_list]

class MyNodeSelector(NodeSelector):

    def __init__(self, call_graph, source_class_color_mapping=DEMO_SOURCE_CLASS_COLOR, sink_class_color_mapping=DEMO_SINK_CLASS_COLOR):
        
        super().__init__(call_graph)

        if not source_class_color_mapping:
            populate_config(CALLERS_FILE, 'source')
            source_class_color_mapping=DEMO_SOURCE_CLASS_COLOR

        if not sink_class_color_mapping:
            populate_config(CALLEES_FILE, 'sink')
            sink_class_color_mapping=DEMO_SINK_CLASS_COLOR

        self.source_class_color_mapping = source_class_color_mapping
        self.sink_class_color_mapping = sink_class_color_mapping

    def select_source_nodes(self, nodes):
        source_nodes = [SourceNode(node_id, color) for (class_name, color) in self.source_class_color_mapping for node_id in nodes if class_name in node_id]
        return source_nodes

    def select_sink_nodes(self, nodes):
        sink_nodes = [SinkNode(node_id, color) for (class_name, color) in self.sink_class_color_mapping for node_id in nodes if class_name in node_id]
        return sink_nodes


class CoreProcessor:

    def __init__(self) -> None:

        jpype.startJVM()

        jpype.addClassPath(CALLGRAPH_JAR_FILE)
        mypackage = jpype.JPackage(CALLGRAPH_PACKAGE)
        MyClass = mypackage.JCallGraph  # pylinst: disable=invalid-name
        self.my_object = MyClass()

        # class_and_methods = self.get_methods()
        # callers_callees_lines = self.colorify_methods(class_and_methods)

    def callers_callees_lines(self, init_first=False, *args):
        if init_first:
            self.call_graph_entries(*args)

        class_and_methods = self.get_methods()
        callees = self.colorify_methods(class_and_methods)
        file_write(CALLERS_FILE, callees)
        callers = self.colorify_methods(class_and_methods)
        file_write(CALLEES_FILE, callers)
        return callers

    def colorify_methods(self, class_and_methods):
        from utils import colors
        import random
        # # result = [f"#{item}={random.choice(colors)}" for item in class_and_methods]
        # result = [f"{item}={random.choice(colors)}" for item in class_and_methods]
        # if len(class_and_methods) >= 10:
        #     result = [f"#{item}={random.choice(colors)}" if i >= 10 else f"{item}={random.choice(colors)}" for i, item in enumerate(class_and_methods)]
        # else:
        #     result = [f"{item}={random.choice(colors)}" for item in class_and_methods]

        num_random_methods = 25

        if len(class_and_methods) >= num_random_methods:
            random_indices = set(random.sample(range(len(class_and_methods)), num_random_methods))
            result = [f"{item}={random.choice(colors)}" if i in random_indices else f"#{item}={random.choice(colors)}" for i, item in enumerate(class_and_methods)]
        else:
            result = [f"#{item}={random.choice(colors)}" for item in class_and_methods]


        return '\n'.join(result)


    def get_methods(self):
        class_and_methods = []
        # print classes + methods utk masing2 class
        complexobj = self.my_object.get_list_classname_methods()
        for class_map in complexobj:
            for class_name, method_list in class_map.items():
                # print(f"Class name: {class_name}")
                for method_name in method_list:
                    # print(f"\tMethod name: {method_name}")
                    class_and_methods.append(f"{class_name}:{method_name}")
        return class_and_methods


    def call_graph_entries(self, output_file: str, jar_files: List[str], filter_packages: List[str]):

        self.output_file = output_file

        # daftar class:methods supaya gak terlalu banyak dan gak hitung dari libraries
        self.filter_packages = filter_packages

        # ['file1.jar', 'file2.jar']
        self.jar_files = jar_files

        # buat args daftar jar files
        string_array = jpype.JArray(jpype.JString, 1)(self.jar_files)
        for i in range(len(self.jar_files)): 
            string_array[i] = jpype.JString(self.jar_files[i])

        # kembalian = self.my_object.panggil(string_array, ['javaapplication1'])
        kembalian = self.my_object.panggil(string_array, self.filter_packages)
        kembalian = str(kembalian)
        selected_lines_for_methodcalls = kembalian.splitlines()
        return selected_lines_for_methodcalls

    def run(self, output_file: str, jar_files: List[str], filter_packages: List[str]):
        
        G = nx.DiGraph()

        selected_lines_for_methodcalls = self.call_graph_entries(output_file, jar_files, filter_packages)
        for line in selected_lines_for_methodcalls:
            # skip any class or methods that have $ in their names
            if line.startswith("M:") and not '$' in line:
                source = extract_nx_source_name(line)
                G.add_node(source)
                target = extract_nx_target_name(line)
                G.add_node(target)
                G.add_edge(source, target)

        graphnodes = G.nodes()
        print(f"""
        Num of nodes: {len(graphnodes)}
        """)

        node_selector = MyNodeSelector(G)
        source_nodes = node_selector.source_nodes()
        sink_nodes = node_selector.sink_nodes()

        net = Network(width='100%', height='768px', directed=True)

        # One source node can point to many sink nodes
        for source in source_nodes:
            for sink in sink_nodes:
                for path in nx.all_simple_paths(G, source=source.id, target=sink.id):
                    net.add_node(source.display_name, title=source.display_name, color=source.color)
                    net.add_node(sink.display_name, title=sink.display_name, color=sink.color)
                    net.add_edge(source.display_name, sink.display_name, color=sink.edge_color(), title=sink.edge_label())
        net.toggle_physics(False)
        # # Visualization
        # net.show_buttons()
        # output_file = call_graph_file_name+'.html'
        # net.write_html(output_file)
        net.save_graph(f'{self.output_file}.html')


if __name__ == '__main__':
    # input('Press any key when ready... ')
    args = ['JavaApplication1.jar']
    process = CoreProcessor(args, ['javaapplication1'])
    process.run()
