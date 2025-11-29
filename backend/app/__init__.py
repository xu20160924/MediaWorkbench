import logging
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from app.api import image, note, prompt, translate, static, health, workflow, user, agent, advertisement_task, image_locations, system_config, filesystem, crawler

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
from app.extensions import db
from app.scheduler import scheduler
from conf import DATABASE_URI
from app.models.agent import Agent, AgentStatus
from app.models.note import Note  # Import Note model so it gets registered
from app.models.task_rule_card import TaskRuleCard  # Import TaskRuleCard model
from app.models.image import ImageDefaultLocation  # Import ImageDefaultLocation model so it gets registered


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

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
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,PATCH,OPTIONS')
        return response
    
    # Initialize Flask-Migrate
    Migrate(app, db)

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
    app.register_blueprint(advertisement_task.bp)
    app.register_blueprint(image_locations.bp)
    app.register_blueprint(system_config.bp)
    app.register_blueprint(filesystem.bp)
    app.register_blueprint(crawler.bp)

    # Initialize running agents
    # with app.app_context():
    #     running_agents = Agent.query.filter_by(status=AgentStatus.RUNNING).all()
    #     for agent1 in running_agents:
    #         scheduler.schedule_agent(agent1)

    return app