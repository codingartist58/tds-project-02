# TDS PROJECT 02

## uvicorn command

uvicorn utils.main:app --port 8020 --reload

## curl command

pdf data
curl "http://localhost:8020/api/" -F "questions.txt=@question.txt" -F "read-pdf.pdf=@sample_table.pdf"

curl "http://localhost:8020/api/" -F "questions.txt=@question.txt" -F "read-pdf.pdf=@read-pdf.pdf"

movies data
curl -X POST "http://localhost:8020/api/" \
  -F "file1=@questions.txt" \
  -F "file2=@movies.csv"


sales data
curl "http://localhost:8020/api/" -F "questions.txt=@questions.txt" -F "sales-data.csv=@sample-sales.csv"

curl "http://localhost:8020/api/" -F "questions.txt=@questions.txt" -F "data.csv=@data.csv"


curl "http://localhost:8020/api/" -F "questions.txt=@questions.txt" -F "image.png=@image.png" -F "data.csv=@data.csv"

curl -X POST "http://localhost:8020/api/"   -F "file=@samples/questions.txt"

curl -X POST "http://localhost:8020/api/"   -F "questions=@samples/questions.txt" -F "attachments=@samples/data.csv"


