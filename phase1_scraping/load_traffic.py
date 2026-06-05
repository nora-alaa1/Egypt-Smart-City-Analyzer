import osmnx as ox
import psycopg2

print('Downloading Alexandria road network...')
ox.settings.overpass_endpoint = "https://overpass.kumi.systems/api/interpreter"
G = ox.graph_from_place('Alexandria, Egypt', network_type='drive')
nodes, edges = ox.graph_to_gdfs(G)
nodes = nodes.reset_index()
edges = edges.reset_index()

conn = psycopg2.connect(host='postgres', port=5432, dbname='smartcity', user='smartcity', password='smartcity123')
cur = conn.cursor()

print(f'Loading {len(nodes)} nodes...')
for _, row in nodes.iterrows():
    cur.execute('INSERT INTO bronze.traffic_nodes (osmid, x, y, geometry) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
        (str(row.get('osmid','')), float(row.get('x',0)), float(row.get('y',0)), str(row.get('geometry',''))))

print(f'Loading {len(edges)} edges...')
for _, row in edges.iterrows():
    cur.execute('INSERT INTO bronze.traffic_edges (u, v, key, geometry) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
        (str(row.get('u','')), str(row.get('v','')), str(row.get('key','')), str(row.get('geometry',''))))

conn.commit()
print('Done!')
conn.close()