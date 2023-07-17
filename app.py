from flask import Flask, render_template, request, redirect, url_for, jsonify
from supabase import create_client, Client 
from markdown import markdown ## For converting markdown to html
from dotenv import load_dotenv ## For loading the .env file with environment variables
from markupsafe import escape ## for escaping potentially dangerous code
from html import unescape ## Unescape to render
import os

load_dotenv()

app = Flask(__name__) 
app.secret_key = "secret" 

def setup_superbase():
	url: str = os.getenv('SUPABASE_URL')
	key: str = os.getenv('SUPABASE_KEY')
	supabase: Client = create_client(url, key) 
	return supabase

def get_all_posts(supabase):
	posts = supabase.table('Posts').select("*").execute().data
	return posts

def get_specific_post(post_id):
	supabase = setup_superbase()
	try:
		response = supabase.table('Posts').select("*").eq('id', f'{post_id}').execute()
		return response.data[0]
	except:
		return "An error occurred"

def read_and_post(type, post_id=0):
	# get and sanitize form data 
	title = escape(request.form.get('title'))
	category = escape(request.form.get('category'))
	description = escape(request.form.get('snippet_description'))
	first_part = escape(request.form.get('first_part_of_content'))
	second_part = escape(request.form.get('second_part_of_content'))

	# Connect to Supabase
	supabase = setup_superbase()

	if type == 'insert':
		# Insert Data
		data, count = supabase.table("Posts").insert({
			"title":title, 
			"category": category, 
			"snippet_description":description,
			"first_part_content": first_part,
			"second_part_content": second_part

			}).execute()
	else:
		data, count = supabase.table("Posts").update({
			"title":title, 
			"category": category, 
			"snippet_description":description,
			"first_part_content": first_part,
			"second_part_content": second_part
			}).eq('id', f'{post_id}').execute()

@app.route('/')
def index():
	supabase = setup_superbase()
	data = get_all_posts(supabase)
	return render_template('index.html', data=data, pagename='index') 

@app.route('/<post_id>')
def single_post(post_id):
	response = get_specific_post(post_id)
	post_content = ""

	# concat the parts and render the post
	if response['second_part_content'] != None:
		#Convert markdown to HTML
		post_content = markdown(unescape(response['first_part_content'] + "\n\n" + response['second_part_content']))
	else:
		post_content = markdown(unescape(response['first_part_content']))

	return render_template('single-post-page.html',pagename='Blog Post', post_id=post_id, post_title=unescape(response['title']), post_content=post_content, category= response["category"]) 

@app.route("/about")
def about():
	return render_template('about.html', pagename='About')

@app.route("/categories")
def categories():
	return render_template('categories.html', pagename='Post categories')

@app.route("/contact")
def contact():
	return render_template('contact.html', pagename='Contact')



# Backend Homepage -> FUNCTIONAL
@app.route("/backend")
def admin_home():
	supabase = setup_superbase() 
	data = get_all_posts(supabase) 
	return render_template('backend.html', data=data) 


# Read the post as admin (TODO: Implement SEO friendly links) -> FUNCTIONAL
@app.route("/backend/post/<post_id>") 
def admin_view_post(post_id): #Use postname for front-end and POST id for backend
	supabase = setup_superbase() 
	# return f"{post_id}"
	# check if there's such a post 
	try:
		response = supabase.table('Posts').select("*", count="exact").eq('id', f'{post_id}').execute()
	except:
		return "An error occurred"

	post_content = ""

	if response.count == 1:
		# concat the parts and render the post
		if response.data[0]['second_part_content'] != None:
			#Convert markdown to HTML
			post_content = markdown(response.data[0]['first_part_content'] + "\n" + response.data[0]['second_part_content'])
		else:
			post_content = markdown(response.data[0]['first_part_content'])

	else:
		return 'Post not found'

	return render_template('admin_post_view.html', post_id=post_id, post_title=response.data[0]['title'], post_content=post_content)


# CREATE new post -> FUNCTIONAL (HANDLE XSS)
@app.route('/backend/create-post', methods=['GET', 'POST'])
def admin_create_post():
	# check method
	if request.method == "POST":
		read_and_post('insert')
		# redirect to the newly created post 
		return redirect(url_for('admin_home'))
	
	# else: just render the create page html 
	return render_template('create-post.html')


# EDIT post -> FUNCTIONAL (make it more efficient by reducing routes)
@app.route('/backend/post/<post_id>/edit-post', methods= ['GET', 'POST'])
def admin_update_post(post_id):
	if request.method == 'GET':
		data = get_specific_post(post_id)
		return render_template('post-editor.html', post_data=data)

	if request.method == 'POST':
		read_and_post("update", post_id)
		# redirect to the newly created post 
		return redirect(url_for('admin_view_post', post_id=post_id))


# DELELTE POST -> SEMI-FUNCTIONAL (need to fix redirecting and figure out what to return)
@app.route('/backend/post/<post_id>/delete-post', methods=['POST'])
def admin_delete_post(post_id):
	supabase = setup_superbase()
	data, count = supabase.table("Posts").delete().eq("id", f"{post_id}").execute()
	return redirect(url_for("admin_home"))

# @app.route('/register', methods=["GET","POST"])
# def register():
# 	if request.method == "POST":

# 		supabase = setup_superbase()

# 		random_email: str = escape(request.form.get("email"))
# 		random_password: str = escape(request.form.get("password"))

# 		user = supabase.auth.sign_up({ "email": random_email, "password": random_password})

# 		return f"{user}"

# 	return render_template("register.html")

# @app.route("/private") # Only be able to access this page if authenticated as admin
# def private_page():
# 	return "PRIVATE PAGE"

if __name__ == "__main__":
	app.run()