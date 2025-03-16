# Events Package

The `events` package provides a robust and flexible event dispatching system. It includes mechanisms for sending signals, connecting receivers, and handling errors gracefully. This package is designed to be used in applications where decoupled communication between components is necessary.

## Table of Contents

- **[Usage](#usage)** 
  - [Sending Signals](#sending-signals)
  - [Connecting Receivers](#connecting-receivers)
  - [Error Handling](#error-handling)
  - [Middleware](#middleware)


- **[API Reference](#api-reference)**
  - [send](#send)
  - [async_send](#async_send)
  - [threaded_send](#threaded_send)
  - [getReceivers](#getReceivers)
  - [liveReceivers](#liveReceivers)
  - [getAllReceivers](#getAllReceivers)

## Usage
Here you go. . . 

### Sending Signals
You can send signals to all connected receivers using the send, async_send, or threaded_send functions.

*Example:*
```python
from runecaller.events.dispatcher import send

# Send a signal
responses = send(signal="my_signal", sender="my_sender", arg1="value1", arg2="value2")
```



### Connecting Receivers
Receivers are functions or methods that are connected to signals. They are called when a signal is sent.

*Example:*
```python
    from runecaller.events.dispatcher import connect
    
    def my_receiver(signal, sender, **kwargs):
        print(f"Received signal: {signal} from sender: {sender} with kwargs: {kwargs}")
    
    # Connect the receiver to a signal
    connect(receiver=my_receiver, signal="my_signal", sender="my_sender")
```

### Error Handling
The **events** package includes robust error handling mechanisms. If a receiver raises an exception, it is caught and logged.

### Middleware
You can add middleware to process signals before they are sent to receivers.

*Example:*
```python
    from runecaller.events.dispatcher import add_middleware
    
    def my_middleware(signal, sender, **kwargs):
        print(f"Middleware processing signal: {signal}")
        return signal, sender, kwargs
    
    # Add middleware
    add_middleware(my_middleware)
```

## API Reference

### send
```python
  async def send(signal: Any = Any, sender: Any = None, *arguments, **named) -> List[Tuple[Callable, Any]]:
      """Send a signal asynchronously to all connected receivers."""
```

### async_send
```python
  async def async_send(signal: Any = Any, sender: Any = None, *arguments, **named) -> List[Tuple[Callable, Any]]:
      """Send a signal asynchronously to all connected receivers using a queue."""
```

### threaded_send
```python
  def threaded_send(signal: Any = Any, sender: Any = None, *arguments, **named) -> List[Tuple[Callable, Any]]:
      """Send a signal to all connected receivers using multiple threads."""
```

### getReceivers
```python
  def getReceivers(sender: Any, signal: Any) -> List[Callable]:
      """Retrieve the list of receivers for a given sender and signal."""
```

### liveReceivers
```python
  def liveReceivers(receivers: List[Union[Callable, weakref.ReferenceType]]) -> Callable:
      """Yield live receivers from a list of receivers."""
```

### getAllReceivers
```python
  def getAllReceivers(sender: Any = Any, signal: Any = Any) -> Callable:
      """Retrieve all receivers for a given sender and signal, including wildcards."""
```