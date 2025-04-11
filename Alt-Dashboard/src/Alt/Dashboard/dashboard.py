from flask import Flask, render_template
from flask_socketio import SocketIO
import asyncio
import threading
from .AgentManager import AgentManager, AgentSubscription


def main():
    print(f"-----------------------------Starting-Dashboard-----------------------------")
    app = Flask(__name__)
    socketio = SocketIO(app, async_mode='threading')

    manager = AgentManager()


    @app.route('/')
    def index():
        return render_template('index.html')

    async def status_updater():
        


        while True:
            allRunningAgents = set(manager.getAllRunningAgents())
            curRunningAgents = set(manager.getCurrentlyRunningAgents())


            statuses = []

            for agent in allRunningAgents:
                status = {}
                agentSubcription = manager.getSubscription(agent)
                status["name"] = agent
                status["active"] = "Active" if agent in curRunningAgents else "Inactive"
                status["status"] = agentSubcription.getStatus()
                status["description"] = agentSubcription.getDescription()
                status["errors"] = agentSubcription.getErrors()
                status["capabilites"] = list(agentSubcription.getCapabilites())

                for timerSub in AgentSubscription.TIMERSUBBASES:
                    status[timerSub] = agentSubcription.getTimer(timerSub)

                status["streamIp"] = agentSubcription.getStreamIp()
                status["streamShape"] = list(agentSubcription.getStreamShape())

                statuses.append(status)

            socketio.emit('status_update', statuses)
            await asyncio.sleep(0.05)

    def start_background_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(status_updater())

    # Launch background task in separate thread with its own event loop
    threading.Thread(target=start_background_task, daemon=True).start()

    socketio.run(app, debug=True, port=9000)


if __name__ == "__main__":
    main()