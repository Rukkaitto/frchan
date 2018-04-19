from flask import Flask, request, render_template, g
from werkzeug.utils import secure_filename
import sqlite3, datetime, os, random

DATABASE = '/home/Rukkaitto/4chan/chan.db'
UPLOAD_FOLDER = '/home/Rukkaitto/4chan/static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'webm'])
SITE_NAME = 'frchan'

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    boards = query_db("select * from boards order by board_short_name asc")
    return render_template('homepage.html', boards=boards, site_name=SITE_NAME)

@app.route('/<board>')
def board(board):
    boards = query_db("select * from boards order by board_short_name asc")
    board_name = query_db('select board_description from boards where board_short_name="{}"'.format(board))
    posts = query_db('select * from posts where board="{}"'.format(board))
    return render_template('board.html', posts=posts, board=board, site_name=SITE_NAME, boards=boards, board_name=board_name[0][0])

@app.route('/<board>/post', methods = ['POST'])
def post(board):
    filename = ''
    if 'image' in request.files:
        filename = upload_image(request.files['image'])

    now = datetime.datetime.now()
    name = request.form.get('name')
    post_text = request.form.get('post_text')
    if post_text == '':
        return 'Empty post: not allowed'

    if filename=='':
        return 'Error: no file selected'

    if name=='':
        name='Anonymous'

    post = (name,now.isoformat(),board,post_text,filename)

    print (create_post(post))
    return render_template('post_successful.html', board=board)

@app.route('/<board>/replies/<post_id>')
def reply(board, post_id):
    replies = query_db('select * from replies where replying_to="{}"'.format(str(post_id)))

    return render_template('replies.html', board=board, post_id=post_id, replies=replies)

@app.route('/<board>/replies/<post_id>/post', methods = ['POST'])
def post_reply(board, post_id):
    filename = ''
    if 'image' in request.files:
        filename = upload_image(request.files['image'])

    now = datetime.datetime.now()
    name = request.form.get('name')
    post_text = request.form.get('post_text')

    if name=='':
        name='Anonymous'

    post = (name,now.isoformat(),board,post_text,filename,post_id)
    print (create_reply(post))
    return render_template('post_successful.html', board=board)

def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def create_post(request):
    query = ''' INSERT INTO posts(user, date, board, post_text, image_file) values (?,?,?,?,?) '''
    cur = get_db().cursor()
    cur.execute(query, request)
    get_db().commit()
    cur.close()
    return cur.lastrowid

def create_reply(request):
    query = ''' INSERT INTO replies(user, date, board, post_text, image_file, replying_to) values (?,?,?,?,?,?) '''
    cur = get_db().cursor()
    cur.execute(query, request)
    get_db().commit()
    cur.close()
    return cur.lastrowid

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(image):
    filename=''
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        newfilename = str(random.randint(10000,100000))+'.'+filename.rsplit('.',1)[1].lower()
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], newfilename))
    return newfilename