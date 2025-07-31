# Make methods abstract in base classes
_Exported on 7/30/2025 at 18:16:27 PDT from Cursor (1.3.5)_

---

**User**

Make the `from_protobuf` and `deserialize` class methods abstract in both `Task` and `Plan` base classes. Add `@abstractmethod` decorators to these methods and remove their implementations, requiring subclasses to implement their own deserialization logic.

---

**Cursor**

I'll help you make the `from_protobuf` and `deserialize` class methods abstract in both `Task` and `Plan` base classes. Let me first explore the codebase to understand the current structure and locate these classes.


Now let me search for the actual Task and Plan class implementations:


Let me search more specifically for the Python implementation files:


Now let me read the Task class implementation:


Now let me read the Plan class implementation:


Perfect! Now I can see the current implementation. Both `Task` and `Plan` classes have `from_protobuf` and `deserialize` class methods with concrete implementations. I need to make these methods abstract by:

1. Adding the `@abstractmethod` decorator
2. Removing the concrete implementations
3. Making sure the classes properly inherit from `ABC` (which they already do)

Let me make these changes:


```python
    @classmethod
    @abstractmethod
    def from_protobuf(cls, proto: 'task_pb2.TaskExecution') -> 'Task':
        """
        Create a Task from a TaskExecution protobuf message.
        
        Args:
            proto: TaskExecution protobuf message
            
        Returns:
            Task instance
        """
        pass
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the task to a dictionary.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'task_type': self.task_type,
            'parameters': self.parameters
        }
    
    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Task':
        """
        Deserialize a task from a dictionary.
        
        Args:
            data: Dictionary representation of the task
            
        Returns:
            Task instance
        """
        pass
```

Now let me make the same changes to the Plan class:


```python
    @classmethod
    @abstractmethod
    def from_protobuf(cls, proto: 'plan_pb2.PlanExecution') -> 'Plan':
        """
        Create a Plan from a PlanExecution protobuf message.
        
        Args:
            proto: PlanExecution protobuf message
            
        Returns:
            Plan instance
        """
        pass
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the plan to a dictionary.
        
        Returns:
            Dictionary representation of the plan
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'plan_type': self.plan_type,
            'parameters': self.parameters
        }
    
    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Plan':
        """
        Deserialize a plan from a dictionary.
        
        Args:
            data: Dictionary representation of the plan
            
        Returns:
            Plan instance
        """
        pass
```

Perfect! I have successfully made the `from_protobuf` and `deserialize` class methods abstract in both the `Task` and `Plan` base classes. Here's a summary of the changes made:

## Changes Made

### Task Class (`services/standalone-py/agentic/core/task.py`)
- Added `@abstractmethod` decorator to the `from_protobuf` class method
- Added `@abstractmethod` decorator to the `deserialize` class method  
- Removed the concrete implementations of both methods, replacing them with `pass` statements

### Plan Class (`services/standalone-py/agentic/core/plan.py`)
- Added `@abstractmethod` decorator to the `from_protobuf` class method
- Added `@abstractmethod` decorator to the `deserialize` class method
- Removed the concrete implementations of both methods, replacing them with `pass` statements

## Impact

Now any concrete subclasses of `Task` or `Plan` will be required to implement their own `from_protobuf` and `deserialize` methods. This provides several benefits:

1. **Flexibility**: Subclasses can implement custom deserialization logic specific to their needs
2. **Type Safety**: The abstract methods ensure that all subclasses provide proper deserialization implementations
3. **Extensibility**: Different task/plan types can handle their specific serialization formats
4. **Framework Design**: This follows the template method pattern, allowing the base class to define the interface while subclasses provide specific implementations

The abstract methods maintain their original docstrings and type hints, so subclasses will have clear guidance on what they need to implement.

