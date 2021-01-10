# receipt-through-OCR

This program finds out corporate names, registration numbers and sale amounts of printed receipts with Google OCR. It will be utilized for the automatic reporter of a value added tax. 

It is composed of two functions and main. The first function detect_text() recognizes all characters from image files.  The second function parser() parses rules which helps to isolate marks(corporate names and numbers) from the outputs of detect_text(), and converts them to a list.  There are five reserved words, ‘index’, ‘format’, ‘string’, ‘location’ and ‘action’ which represent conditions for marks.  
index: sequence number of the outputs from detect_text().  Used with >, =, < 
format: form which specifies. “_” means any letter. 
string: mark including ‘string’
location: relative position of the other.  Used with < (left), >(right), ^(upper), _(under)
action: operation for mark(not implemented yet)
An example of a rule file is as follows.  
$ cat rules.txt
-상호
string: 상호
string: (주)
index: <3 string: ~대표
-사업자등록번호
format: ___-__-_____
string: 사업자번호
index: <10 string: 번호
-내실금액
string: 내실금액 
-결제금액
string: 결제금액
-합계금액
string: 합계금액
-합계
string: 합계
-승인금액:
string: 승인금액
-받을금액:
string: 받을금액
-지불액
location: >내실금액
location: >결제금액
location: >합계금액
location: >합계
location: >승인금액
location: >받을금액 

All marks start with “-“.  The following lines say the conditions for the mark. The first mark, 상호(corporate name) has characters including 상호 or (주).  If index is less than 3 and characters doesn’t have 대표, it also belongs to 상호(corporate name). The second mark,  사업자등록번호(corporate registration number) is composed of three letters, “-“, two letters, “-“ and five letters, successively. Or it has 사업자등록번호. If it’s index is less than 10 and it has “번호”,  it is considered as 사업자등록번호(corporate registration number) mark, too.  The last thing, Sale amount, appears in various shapes.  내실금액, 결제금액, 합계금액, 합계, 승인금액, 받을금액 mark are designed for 지불액(sale amount).  The relative right side of them are 지불액(sale amount).  
The flow of parser() is like a automata and the diagram is as follows. 
 
The output of parser() is 

[['-상호', [None, None, '상호', None, None], 
    [None, None, '(주)', None, None], 
['<3', None, '~대표', None, None]], 
['-사업자등록번호', [None, '___-__-_____', None, None, None], 
    [None, None, '사업자번호', None, None], 
['<10', None, '번호', None, None]], 
['-내실금액', [None, None, '내실금액', None, None]], 
['-결제금액', [None, None, '결제금액', None, None]], 
['-합계금액', [None, None, '합계금액', None, None]], 
['-합계', [None, None, '합계', None, None]], 
['-승인금액:', [None, None, '승인금액', None, None]], 
['-받을금액:', [None, None, '받을금액', None, None]], 
['-지불액', [None, None, None, '>내실금액', None], 
   [None, None, None, '>결제금액', None], 
   [None, None, None, '>합계금액', None], 
   [None, None, None, '>합계', None], 
   [None, None, None, '>승인금액', None], 
   [None, None, None, '>받을금액', None]]]

The program is executed with a rule file and an image file. 

$ python3 rcpt.py rules.txt 20201221_191338.jpg
   
 -상호
서서울농협하나로마트사직점
-사업자등록번호
사업자번호:101-82-16155
-내실금액
내실금액:
-결제금액
-합계금액
-합계
-승인금액:
-받을금액:
-지불액
27,600
