# 描画
import matplotlib.pyplot as plt
# plt.figure(figsize=(10, 8), constrained_layout=True)
# pos = nx.nx_agraph.graphviz_layout(G, prog="dot")  # `dot` はツリー風にレイアウト
# nx.draw(G, pos, with_labels=True, arrows=True, node_size=1500, node_color="lightblue", font_size=10)
# plt.title("Task Dependency DAG")
# plt.tight_layout()
# plt.savefig("graph.png")
fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
nx.draw(G, pos=nx.spring_layout(G), with_labels=True, arrows=True, ax=ax)
plt.savefig("graph.png")