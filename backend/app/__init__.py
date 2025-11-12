from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from app.api import image, note, prompt, translate, static, health, workflow, user, agent
from app.scheduler import scheduler
from app.models.agent import Agent, AgentStatus
from app.extensions import db

def create_app():
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["*"],
            "expose_headers": ["*"],
            "supports_credentials": True
        }
    })
    
    # Handle OPTIONS method for all routes
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Initialize Flask-Migrate
    migrate = Migrate()
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(image.bp)
    app.register_blueprint(note.bp)
    app.register_blueprint(prompt.bp)
    app.register_blueprint(translate.bp)
    app.register_blueprint(static.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(workflow.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(agent.bp)

    # Initialize running agents
    # with app.app_context():
    #     running_agents = Agent.query.filter_by(status=AgentStatus.RUNNING).all()
    #     for agent1 in running_agents:
    #         scheduler.schedule_agent(agent1)

    return app