import pandas as pd
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import math

app = Flask(__name__)
DATABASE = 'c:/Users/user/workspaces/coding_assistant3/ch08/portfolio.db'
PER_PAGE = 5

def get_db_conn():
    """데이터베이스 연결을 생성하고 row_factory를 설정합니다."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """데이터베이스 테이블을 생성하고 Excel 데이터로 초기화합니다."""
    with app.app_context():
        db = get_db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stocks'")
        if cursor.fetchone() is None:
            cursor.execute('''
                CREATE TABLE stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    company TEXT NOT NULL,
                    shares INTEGER NOT NULL,
                    price REAL NOT NULL,
                    market_value REAL NOT NULL,
                    last_updated TEXT NOT NULL
                );
            ''')
            try:
                df = pd.read_excel('C:/Users/user/workspaces/coding_assistant3/stock.xls')
                for index, row in df.iterrows():
                    cursor.execute(
                        "INSERT INTO stocks (ticker, company, shares, price, market_value, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
                        (row['ticker'], row['company'], int(row['shares']), float(row['price']), float(row['market_value']), row['last_updated'])
                    )
                db.commit()
                print("데이터베이스가 초기화되고 데이터가 로드되었습니다.")
            except FileNotFoundError:
                print(f"오류: Excel 파일을 찾을 수 없습니다.")
            except Exception as e:
                print(f"Excel 로드 중 오류: {e}")
        else:
            print("데이터베이스가 이미 존재합니다.")
        db.close()

@app.route('/')
def index():
    """주식 목록을 표시하며, 검색, 정렬, 페이지네이션을 지원합니다."""
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    page = request.args.get('page', 1, type=int)

    params = []
    base_query = "FROM stocks"
    where_clause = ""
    if search_query:
        where_clause = " WHERE company LIKE ? OR ticker LIKE ?"
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    allowed_sort_by = ['id', 'company', 'shares', 'price', 'market_value', 'last_updated']
    if sort_by not in allowed_sort_by:
        sort_by = 'id'
    order = 'desc' if order.lower() == 'desc' else 'asc'
    
    order_by_clause = f" ORDER BY {sort_by} {order}"

    conn = get_db_conn()
    
    count_query = f"SELECT COUNT(id) {base_query}{where_clause}"
    total_items = conn.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / PER_PAGE)

    offset = (page - 1) * PER_PAGE
    limit_clause = f" LIMIT {PER_PAGE} OFFSET {offset}"
    main_query = f"SELECT * {base_query}{where_clause}{order_by_clause}{limit_clause}"
    stocks = conn.execute(main_query, params).fetchall()
    conn.close()

    def iter_pages(left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, total_pages + 1):
            if num <= left_edge or \
               (num > page - left_current - 1 and num < page + right_current) or \
               num > total_pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    pagination = {
        'page': page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'prev_num': page - 1,
        'has_next': page < total_pages,
        'next_num': page + 1,
        'iter_pages': iter_pages
    }

    return render_template('index.html', stocks=stocks, pagination=pagination, request=request)"FROM stocks"
    where_clause = ""
    if search_query:
        where_clause = " WHERE company LIKE ? OR ticker LIKE ?"
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    allowed_sort_by = ['id', 'company', 'shares', 'price', 'market_value', 'last_updated']
    if sort_by not in allowed_sort_by:
        sort_by = 'id'
    order = 'desc' if order.lower() == 'desc' else 'asc'
    
    order_by_clause = f" ORDER BY {sort_by} {order}"

    conn = get_db_conn()
    
    count_query = f"SELECT COUNT(id) {base_query}{where_clause}"
    total_items = conn.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / PER_PAGE)

    offset = (page - 1) * PER_PAGE
    limit_clause = f" LIMIT {PER_PAGE} OFFSET {offset}"
    main_query = f"SELECT * {base_query}{where_clause}{order_by_clause}{limit_clause}"
    stocks = conn.execute(main_query, params).fetchall()
    conn.close()

    pagination_items = get_pagination_items(page, total_pages)

    pagination = {
        'page': page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'prev_num': page - 1,
        'has_next': page < total_pages,
        'next_num': page + 1,
        'items': pagination_items
    }

    return render_template('index.html', stocks=stocks, pagination=pagination, request=request)

@app.route('/add', methods=['GET', 'POST'])
def add():
    """새 주식 정보를 추가합니다."""
    if request.method == 'POST':
        company = request.form['company']
        ticker = request.form['ticker']
        shares = int(request.form['shares'])
        price = float(request.form['price'])
        
        market_value = shares * price
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_conn()
        conn.execute(
            'INSERT INTO stocks (company, ticker, shares, price, market_value, last_updated) VALUES (?, ?, ?, ?, ?, ?)',
            (company, ticker, shares, price, market_value, last_updated)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('form.html', title='새 주식 추가', stock=None)

@app.route('/edit/<int:stock_id>', methods=['GET', 'POST'])
def edit(stock_id):
    """기존 주식 정보를 수정합니다."""
    conn = get_db_conn()
    
    if request.method == 'POST':
        company = request.form['company']
        ticker = request.form['ticker']
        shares = int(request.form['shares'])
        price = float(request.form['price'])
        
        market_value = shares * price
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            'UPDATE stocks SET company = ?, ticker = ?, shares = ?, price = ?, market_value = ?, last_updated = ? WHERE id = ?',
            (company, ticker, shares, price, market_value, last_updated, stock_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    stock = conn.execute('SELECT * FROM stocks WHERE id = ?', (stock_id,)).fetchone()
    conn.close()
    return render_template('form.html', title='주식 정보 수정', stock=stock)

@app.route('/delete/<int:stock_id>', methods=['POST'])
def delete(stock_id):
    """주식 정보를 삭제합니다."""
    conn = get_db_conn()
    conn.execute('DELETE FROM stocks WHERE id = ?', (stock_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
