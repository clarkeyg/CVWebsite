from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Portfolio data - you can move this to a separate JSON file or database later
PORTFOLIO_DATA = {
	'personal_info': {
		'name': 'George Clarke',
		'title': 'Software Engineer | Embedded Systems | Image Processing',
		'location': 'Oxford, UK',
		'email': 'ClarkeGeorge2003@gmail.com',
		'phone': '+44 771 546 3505',
		'linkedin': 'https://linkedin.com/in/george-clarke-900a3b238',
		'github': 'https://github.com/clarkeyg',
		'summary': 'Highly motivated Computer Science graduate with expertise in AI, machine learning, and embedded systems. Passionate about creating innovative solutions that bridge the gap between hardware and software.'
	},

	'education': {
		'degree': 'Bachelor of Science in Computer Science',
		'university': 'Oxford Brookes University',
		'grade': '3.6/4.0',
		'period': '09/2022 - 06/2025',
		'alevels': {
			'subjects': 'A-Levels in Maths, Physics, And Computer Science',
			'school': 'The Priory School',
			'grade': '3.4/4.0',
			'period': '09/2020 - 06/2022'
		}
	},

	'experience': [
		{
			'title': 'Software Engineer Intern',
			'company': 'Blackmagic Design Inc.',
			'location': 'Welwyn Garden City, UK',
			'period': '09/2024 - 06/2025',
			'description': 'Currently employed as a Software Engineer Intern at Blackmagic Design, working with a small team of 4 engineers on creating, fixing and adding features using C++. Assisted in testing and verifying image sensor calibrations for hardware testing using Python and C++. Extensive use of XCode, Git, Jira, and Review Board.',
			'icon': 'fas fa-code'
		},
		{
			'title': 'Junior Sushi Chef',
			'company': 'Bentozo Ltd.',
			'location': 'Harpenden, UK',
			'period': '06/2023 - 09/2023',
			'description': 'Previously worked as a junior sushi chef at Bentozo Ltd. with a team of 6/7. This was a valuable experience, helping to build core attributes like work ethic and determination.',
			'icon': 'fas fa-utensils'
		}
	],

	'achievements': [
		{
			'title': 'Nominated for Oxford Brookes Tech Show',
			'description': 'Nominated for Oxford Brookes Tech Show to showcase my dissertation work as only 8 of 150 students were selected to present their work.'
		},
		{
			'title': 'Led a Group to Create a Full Stack App',
			'description': 'Led a team of students to create an expense tracking application which was endorsed by our professor.'
		},
		{
			'title': 'Technically Challenging Dissertation',
			'description': 'As part of my degree, I created a Traffic Light Junction and optimized its efficiency using AI and ML to analyse algorithms using AI and ML to optimise and improve the efficiency of the junction.'
		}
	],

	'skills': {
		'programming': ['C++', 'Python', 'Java', 'SQL'],
		'technologies': ['AI/ML', 'Software Design', 'Mathematics', 'Physics', 'Computer Science'],
		'interests': ['Arduino and microprocessors', 'Artificial Intelligence', 'Internet of Things']
	},

	'projects': [
		{
			'title': 'AI Traffic Light Optimization',
			'description': 'Dissertation project that created a Traffic Light Junction and optimized its efficiency using AI and ML algorithms to analyze and improve traffic flow at complex junctions.',
			'technologies': ['Python', 'AI/ML', 'Computer Vision', 'Optimization'],
			'icon': 'fas fa-traffic-light',
			'github_url': '#',
			'demo_url': '#'
		},
		{
			'title': 'Full Stack Expense Tracker',
			'description': 'Led a group of students to create an expense tracking application with comprehensive features including real-time synchronization and intuitive user interface design.',
			'technologies': ['React', 'Node.js', 'MongoDB', 'Leadership'],
			'icon': 'fas fa-mobile-alt',
			'github_url': '#',
			'demo_url': '#'
		},
		{
			'title': 'Embedded Systems Projects',
			'description': 'Various microprocessor and embedded systems projects involving Arduino, IoT devices, and sensor integrations. Exploring the intersection of hardware and software.',
			'technologies': ['C++', 'Arduino', 'IoT', 'Sensors'],
			'icon': 'fas fa-microchip',
			'github_url': '#',
			'demo_url': '#'
		},
		{
			'title': 'Image Processing Suite',
			'description': 'Advanced image processing algorithms and tools developed during my work on sensor calibrations and computer vision applications, showcasing expertise in digital image manipulation.',
			'technologies': ['Python', 'OpenCV', 'NumPy', 'Computer Vision'],
			'icon': 'fas fa-camera',
			'github_url': '#',
			'demo_url': '#'
		}
	]
}


@app.route('/')
def index():
	"""Main portfolio page"""
	return render_template('index.html', data=PORTFOLIO_DATA)


@app.route('/api/portfolio')
def api_portfolio():
	"""API endpoint to get portfolio data as JSON"""
	return jsonify(PORTFOLIO_DATA)


@app.route('/api/contact', methods=['POST'])
def contact():
	"""Handle contact form submissions (you can extend this)"""
	# This is a placeholder - you can add email sending logic here
	return jsonify({'status': 'success', 'message': 'Thank you for your message!'})


@app.errorhandler(404)
def not_found(error):
	"""Handle 404 errors"""
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
	"""Handle 500 errors"""
	return render_template('500.html'), 500


if __name__ == '__main__':
	# Create templates directory if it doesn't exist
	if not os.path.exists('templates'):
		os.makedirs('templates')
	if not os.path.exists('static'):
		os.makedirs('static')
		os.makedirs('static/css')
		os.makedirs('static/js')
		os.makedirs('static/images')

	app.run(debug=True, host='0.0.0.0', port=5000)