
from openai import OpenAI
import os

from dotenv import load_dotenv
load_dotenv()   

# Set your OpenAI API key
client = OpenAI() #OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Real LLM integration
class OpenAIGenerativeModel:
    def generate(self, prompt):
        response = client.chat.completions.create(
            model="gpt-5",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful agentic AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content


# Memory module
class Memory:
    def __init__(self):
        self.history = []

    def remember(self, interaction):
        self.history.append(interaction)

    def recall(self):
        return self.history[-5:]

# Goal planner
class GoalPlanner:
    def __init__(self, model, memory):
        self.model = model
        self.memory = memory

    def set_goal(self, goal):
        response = self.model.generate(f"My goal is: {goal}. Help me plan.")
        self.memory.remember({"goal": goal, "response": response})
        return response

# Tool simulator
class ToolSimulator:
    def use_tool(self, tool_name, input_data):
        return f"Tool '{tool_name}' used with input '{input_data}'. Result: Success."

# Agentic AI system
class AgenticAI:
    def __init__(self):
        self.model = OpenAIGenerativeModel()
        self.memory = Memory()
        self.planner = GoalPlanner(self.model, self.memory)
        self.tool_simulator = ToolSimulator()

    def interact(self, goal, tool_name=None, tool_input=None):
        plan = self.planner.set_goal(goal)
        tool_result = None
        if tool_name and tool_input:
            tool_result = self.tool_simulator.use_tool(tool_name, tool_input)
        return {
            "plan": plan,
            "recent_memory": self.memory.recall(),
            "tool_result": tool_result
        }

# Example usage
agent = AgenticAI()
result = agent.interact("Build a chatbot for customer support", tool_name="WebSearch", tool_input="Chatbot frameworks")

print("Agentic Plan:", result["plan"])
print("Recent Memory:", result["recent_memory"])
if result["tool_result"]:
    print("Tool Result:", result["tool_result"])
else:
    print("No tool result.")