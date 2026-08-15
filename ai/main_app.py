import tkinter as tk
from tkinter import ttk
from app_state import AppState
from services.camera_service import CameraService, CameraSummary

SEGOE_FONT = "Segoe UI"
from runtime.agent_runtime import AgentEvent

class MainApplicationPage(ttk.Frame):

    def __init__(
        self,
        parent,
        controller=None,
        state: AppState | None = None,
        agent_service=None,
        camera_service=None,
    ):
        super().__init__(parent, padding=25)

        self.controller = controller
        self.state = state or AppState()
        self.agent_service = agent_service
        self.camera_service = camera_service
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Header
        ttk.Label(
            self,
            text="WatchDog Agent",
            font=(SEGOE_FONT, 20, "bold")
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            self,
            text="Desktop Agent",
            font=(SEGOE_FONT, 11)
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 20)
        )

        # Agent Status
        status_frame = ttk.LabelFrame(
            self,
            text="Agent Status",
            padding=15
        )

        status_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 15)
        )

        status_frame.columnconfigure(1, weight=1)

        ttk.Label(
            status_frame,
            text="Property:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 15)
        )

        property_text = ( #TODO: Check the account connected and display it later
            self.state.address or "Unknown property"
        )

        self.property_label = ttk.Label(
            status_frame,
            text=property_text,
        )

        self.property_label.grid(
            row=0,
            column=1,
            sticky="w"
        )

        ttk.Label(
            status_frame,
            text="Agent:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 15),
            pady=(10, 0)
        )

        self.agent_status_label = ttk.Label(
            status_frame,
            text="Stopped"
        )

        self.agent_status_label.grid(
            row=1,
            column=1,
            sticky="w",
            pady=(10, 0)
        )

        # Cameras
        cameras_frame = ttk.LabelFrame(
            self,
            text="Cameras",
            padding=15
        )

        cameras_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            pady=(0, 15)
        )

        cameras_frame.columnconfigure(0, weight=1)
        cameras_frame.rowconfigure(0, weight=1)

        self.camera_list = ttk.Treeview(
            cameras_frame,
            columns=("camera", "status"),
            show="headings",
            height=8
        )

        self.camera_list.heading(
            "camera",
            text="Camera"
        )

        self.camera_list.heading(
            "status",
            text="Status"
        )

        self.camera_list.column(
            "camera",
            width=400
        )

        self.camera_list.column(
            "status",
            width=150
        )

        self.camera_list.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        camera_scrollbar = ttk.Scrollbar(
            cameras_frame,
            orient="vertical",
            command=self.camera_list.yview
        )

        camera_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.camera_list.configure(
            yscrollcommand=camera_scrollbar.set
        )

        
        for camera in self.state.cameras:
            self.camera_list.insert(
                "",
                "end",
                values=(
                    camera.get("name", "Unnamed camera"),
                    "Configured",
                ),
            )

        # AI Agent Controls
        controls_frame = ttk.LabelFrame(
            self,
            text="AI Agent",
            padding=15
        )

        controls_frame.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(0, 15)
        )

        self.ai_status_label = ttk.Label(
            controls_frame,
            text="AI Agent is stopped."
        )

        self.ai_status_label.pack(
            side="left"
        )

        self.start_button = ttk.Button(
            controls_frame,
            text="Start Agent",
            command=self.start_agent
        )

        self.start_button.pack(
            side="right",
            padx=(10, 0)
        )

        self.stop_button = ttk.Button(
            controls_frame,
            text="Stop Agent",
            command=self.stop_agent,
            state="disabled"
        )

        self.stop_button.pack(
            side="right"
        )

        self.update_agent_ui(
            state=self.state.agent_status,
            message="AI Agent is stopped.",
        )

        # Bottom Controls
        button_frame = ttk.Frame(self)

        button_frame.grid(
            row=5,
            column=0,
            sticky="ew"
        )

        ttk.Button(
            button_frame,
            text="Exit",
            command=self.exit_application
        ).pack(
            side="right"
        )

    def _render_camera_rows(self, summaries: list[CameraSummary]) -> None:
        """Displays camera summaries in UI"""
        self.camera_list.delete(*self.camera_list.get_children())

        for summary in summaries:
            self.camera_list.insert(
                "",
                "end",
                values=(
                    summary.name,
                    summary.display_status,
                ),
            )

    # AI AGENT CONTROLS
    def start_agent(self) -> None:
        """
        Ask AgentService to start the real local AI process.

        Do not update labels here. AgentRuntime will emit events
        once startup succeeds, fails, or the health check passes.
        """

        if self.agent_service is None:
            self.update_agent_ui(
                state="error",
                message="Agent controls are not available.",
            )
            return

        self.agent_service.start()

    def stop_agent(self) -> None:
        """
        Ask AgentService to stop the real local AI process.
        """

        if self.agent_service is None:
            return

        self.agent_service.stop()

    def handle_agent_event(
        self,
        event: AgentEvent,
    ) -> None:
        """
        Receive an AgentRuntime event from main.py.

        main.py calls this method on the Tkinter main thread, so it
        is safe to update labels and buttons here.
        """

        if event.event_type == "status":
            self.update_agent_ui(
                state=event.status or "error",
                message=event.message,
            )

        elif event.event_type == "error":
            self.update_agent_ui(
                state="error",
                message=event.message,
            )

        elif event.event_type == "log":
            # The main page does not have an agent log panel yet.
            # We will later display or write these log messages.
            pass

    def update_agent_ui(
        self,
        state: str,
        message: str,
    ) -> None:
        """
        Reflect the actual runtime state in the page.

        This method changes widgets only. It never starts/stops
        a process and never calls AgentRuntime directly.
        """

        self.state.agent_status = state

        self.agent_status_label.config(
            text=state.capitalize(),
        )

        self.ai_status_label.config(
            text=message,
        )

        self.start_button.config(
            state=(
                "normal"
                if state in {"stopped", "crashed", "error"}
                else "disabled"
            )
        )

        self.stop_button.config(
            state=(
                "normal"
                if state in {"starting", "running"}
                else "disabled"
            )
        )

    # APPLICATION
    def exit_application(self) -> None:
        """
        Ask the application controller to begin shutdown.

        The controller owns AgentService and the Tk root, so this page
        must not destroy the root or stop processes directly.
        """

        if self.controller is not None:
            self.controller.quit_application()
            return

        self.winfo_toplevel().destroy()


if __name__ == "__main__":
    root = tk.Tk()

    root.title("WatchDog Agent")
    root.geometry("800x650")

    MainApplicationPage(
        root
    ).pack(
        fill="both",
        expand=True
    )

    root.mainloop()