from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
from .AgentManager import AgentManager, AgentSubscription
from Alt.Core import getChildLogger

Sentinel = getChildLogger("Dashboard_Logger")

def main():
    Sentinel.info(
        f"-----------------------------Starting-Dashboard-----------------------------"
    )
    app = Flask(__name__)
    socketio = SocketIO(app, async_mode="threading")  # remains the same

    manager = AgentManager()

    @app.route("/")
    def index() -> str:
        return render_template("index.html")

    def status_updater() -> None:
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
                status["capabilites"] = list(agentSubcription.getCapabilities())

                for timerSub in AgentSubscription.TIMERSUBBASES:
                    status[timerSub] = agentSubcription.getTimer(timerSub)

                status["streamPaths"] = agentSubcription.getStreamPaths()
                status["logIp"] = agentSubcription.getLogIp()

                statuses.append(status)

            socketio.emit("status_update", statuses)

            time.sleep(0.05)

    # Launch background task in separate thread
    threading.Thread(target=status_updater, daemon=True).start()

    socketio.run(app, host='0.0.0.0', debug=False, use_reloader=False, port=9000)

def mainAsync() -> None:
    Sentinel.info("Starting dasboard on daemon thread...")
    threading.Thread(target=main, daemon=True).start()


if __name__ == "__main__":
    main()
