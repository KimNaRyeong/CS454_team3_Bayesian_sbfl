import pandas as pd

# Excel 파일 경로 설정
excel_file_path = 'test_data2.pkl.xlsx'

# Excel 파일 읽기
df = pd.read_excel(excel_file_path, index_col=0)

# 저장할 .pkl 파일 경로 설정
pkl_file_path = 'test_data2.pkl'

# DataFrame을 .pkl로 저장
df.to_pickle(pkl_file_path)

# print(f"Excel 파일이 성공적으로 {pkl_file_path}로 저장되었습니다!")