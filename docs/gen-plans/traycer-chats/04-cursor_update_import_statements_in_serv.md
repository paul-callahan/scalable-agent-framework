# Update import statements in server.py
_Exported on 7/30/2025 at 18:16:36 PDT from Cursor (1.3.5)_

---

**User**

Add `common_pb2` to the imports in `services/standalone-py/agentic/data_plane/server.py`. Update the import statement on line 19 to include `from ..pb import services_pb2, services_pb2_grpc, common_pb2`.

---

**Cursor**

I'll help you add `common_pb2` to the imports in the data plane server file. Let me first examine the current file to see the existing import statement on line 19.


Now I can see the current import statement on line 19. I need to update it to include `common_pb2`. Let me make the edit:


```python
try:
    from ..pb import services_pb2, services_pb2_grpc
    from ..pb import task_pb2, plan_pb2

->

try:
    from ..pb import services_pb2, services_pb2_grpc, common_pb2
    from ..pb import task_pb2, plan_pb2
```

Perfect! I've successfully updated the import statement on line 19 to include `common_pb2`. The import now reads:

```python
from ..pb import services_pb2, services_pb2_grpc, common_pb2
```

This change adds `common_pb2` to the existing import statement that was already importing `services_pb2` and `services_pb2_grpc` from the `..pb` module.

```python
from ..pb import services_pb2, services_pb2_grpc, common_pb2
```

