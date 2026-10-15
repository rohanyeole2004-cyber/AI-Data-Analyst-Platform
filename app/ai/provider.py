from abc import ABC,abstractmethod
class AIProvider(ABC):
 @abstractmethod
 def plan(self,question,columns):...
class NoLLMProvider(AIProvider):
 def plan(self,question,columns): raise NotImplementedError
