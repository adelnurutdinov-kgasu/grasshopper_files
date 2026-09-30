import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tidy_gen import tidy
# python tidy_perforation.py ../definition/original/perforation_random.gh out.gh
B = {
 'IN': '65fa 7f31 5083 de8b dd21',
 'BIG': '4718 4038 bd63 58e3 becf 1960 5eaa 36a8 1d70 3212 306c c81d b078 00fc 10c2 95e5 47eb 6914 b25c 3b14 1f98 7e2c',
 'PTS': '7c7f c711 0ea1 7e77 f515 f04f 735a f6ef 5e9f 4c7e db70 864d 82ab dc84 7106 8bfa a68f',
 'RAD': '1b2c b1cc 6bda 6bef 1a7b 4866 c338 9461 2566 6f99 ff67 156c a1eb 0be5 553a 9844 da06 39d1',
 'CUT': 'e11b dca2 6ff8 c081 2dbf fa6b 1ecd b6eb f6b3',
 'GRID': 'df1b ce1f 0306 d6cf b722 d53b af4f 00de',
}
M = {p: k for k, v in B.items() for p in v.split()}
T = {'IN': '0 · ВХОД: поверхность панели (Reparameterize → u,v 0…1)',
     'BIG': '1 · КРУПНЫЕ ОТВЕРСТИЯ — световые фонари (кандидаты, отступ от краёв, радиус)',
     'PTS': '2 · МЕЛКИЕ ОТВЕРСТИЯ: точки + отступ от краёв панели',
     'RAD': '3 · РАДИУС МЕЛКИХ = f(расстояние до фонаря) · Graph Mapper · отсев малых',
     'CUT': '4 · ВЫРЕЗКА: Brep|Brep → Surface Split → панель с отверстиями',
     'GRID': 'ПРЕВЬЮ: сетка u,v на поверхности (на результат не влияет)',
     'X': 'НЕ ИСПОЛЬЗУЕТСЯ (случайные точки, Jitter, MD Slider)'}
C = {'IN': '#FFE08A', 'BIG': '#FFB38A', 'PTS': '#9FD3FF', 'RAD': '#B8E6A8', 'CUT': '#F5B7E0', 'GRID': '#DDDDDD', 'X': '#DDDDDD'}
R = {'4038': 'фонари · кандидатов', '1960': 'фонари · отступ по u', '36a8': 'фонари · отступ по v (низ)', '5eaa': 'фонари · отступ по v (верх)',
     '47eb': 'фонари · радиус', 'c711': 'отверстия · кандидатов', '864d': 'отверстия · отступ по u', '82ab': 'отверстия · отступ по v',
     'a1eb': 'отверстия · макс. радиус', '9844': 'отверстия · мин. радиус (отсев)'}
print(tidy(sys.argv[1], sys.argv[2], lambda g: M.get(g[:4], 'X'), T, C, [['IN', 'BIG', 'PTS', 'RAD', 'CUT'], ['GRID', 'X']], R))
