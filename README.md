# MailDealer-Bot

### ※List những vùng cần xử lí:

- 仙台施工
- 郡山施工
- 浜松施工
- 東海施工
- 関西施工
- 岡山施工
- 広島施工
- 福岡施工
- 熊本施工

### Tuy nhiên, có 2 trường hợp đặc biệt:

- 東京施工: nếu địa chỉ trong access (cột 配送先住所) không chứa 1 trong những giá trị này (甲府市、富士吉田市、都留市、山梨市、大月市、韮崎市、南アルプス市、北杜市、甲斐市、笛吹市、上野原市、甲州市、中央市) thì result ghi: vùng không cần làm-> bot không làm các bước tiếp theo
- 神奈川施工: nếu địa chỉ trong access (cột 配送先住所) không chứa 静岡県 thì result ghi: vùng không cần làm-> bot không làm các bước tiếp theo
