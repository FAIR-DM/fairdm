
## 2026-10-08T22:54:13Z · orchestrator · plan and reconciliation

Research, plan and task list written. The task list was written as if no API existed and then
checked against the code: 60 tasks, 7 proven done by cited code and a passing test (T007, T008,
T010, T021, T033, T044, T045), 53 open. Of the open ones, most are open because the behaviour was
never built or fails; the write-path rules from FS-022 are built but tested only through a
hand-made viewset that sends database numbers, so their tasks stay open until tests use the real
routes.
