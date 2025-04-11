from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
from .AgentManager import AgentManager, AgentSubscription


def main():
    print(
        f"-----------------------------Starting-Dashboard-----------------------------"
    )
    app = Flask(__name__)
    socketio = SocketIO(app, async_mode="threading")  # remains the same

    manager = AgentManager()

    @app.route("/")
    def index():
        return render_template("index.html")

    def status_updater():
        while True:
            allRunningAgents = set(manager.getAllRunningAgents())
            curRunningAgents = set(manager.getCurrentlyRunningAgents())

            statuses = []

            for agent in allRunningAgents:
                status = {}
                agentSubcription = manager.getSubscription(agent)
                dotIdx = agent.find(".")
                group = agent[:dotIdx]
                name = agent[dotIdx + 1 :]
                status["group"] = group
                status["name"] = name
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

            import json

            print(f"Payload size: {len(json.dumps(statuses))} bytes")

            socketio.emit("status_update", statuses)

            # Sleep for 500ms instead of 50ms to ease CPU load and avoid frontend spam
            time.sleep(0.1)

    # Launch background task in separate thread
    threading.Thread(target=status_updater, daemon=True).start()

    socketio.run(app, debug=True, port=9000)


if __name__ == "__main__":
    main()
