from zmlc import Router, Task

router = Router()
result = router.solve(Task(prompt="What is 17 + 25?", task_type="math"))
print(result.answer)
print(result.route.value)
print(result.trace)
