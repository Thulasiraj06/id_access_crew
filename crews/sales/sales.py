import os
import yaml
from crewai import Crew, Agent, Task
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SalesCrew:
    def __init__(self, topic: str):
        print("I am sales")
        self.topic = topic
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "sales")
        self.agents_config = self._load_yaml("agents.yaml")
        self.tasks_config = self._load_yaml("tasks.yaml")
        
    def _load_yaml(self, filename: str) -> Dict:
        """Load YAML configuration file"""
        print("loading the yaml")
        config_path = os.path.join(self.config_dir, filename)
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create agents from configuration"""
        print("creating agents")
        agents = []
        for agent_config in self.agents_config.get("agents", []):
            agent = Agent(
                role=agent_config.get("role"),
                goal=agent_config.get("goal"),
                backstory=agent_config.get("backstory"),
                verbose=agent_config.get("verbose", True),
                allow_delegation=agent_config.get("allow_delegation", False),
                max_rpm=agent_config.get("max_rpm", 10),
                # Use the correct model specification format
                llm="gpt-4-turbo-preview"  # Directly specify the model name as a string
            )
            agents.append((agent_config.get("name"), agent))
        
        return dict(agents)
    
    def _create_tasks(self, agents: Dict[str, Agent]) -> List[Task]:
        """Create tasks from configuration"""
        print("creating tasks")
        tasks = []
        task_dict = {}
        
        for task_config in self.tasks_config.get("tasks", []):
            # Format the description with the topic
            description = task_config.get("description").format(topic=self.topic)
            
            task = Task(
                description=description,
                agent=agents[task_config.get("agent")],
                expected_output=task_config.get("expected_output")
            )
            task_dict[task_config.get("name")] = task
            tasks.append(task)
        
        # Set up task dependencies
        for i, task_config in enumerate(self.tasks_config.get("tasks", [])):
            context_tasks = [task_dict[ctx] for ctx in task_config.get("context", [])]
            if context_tasks:
                tasks[i].context = context_tasks
        
        return tasks
    
    def run(self) -> str:
        """Run the sales crew"""
        print("running")
        agents = self._create_agents()
        tasks = self._create_tasks(agents)
        
        # Create a Crew with the agents and tasks
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            verbose=True
        )
        
        # Run the crew
        result = crew.kickoff()
        return result