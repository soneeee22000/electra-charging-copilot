# Why this exists

**A wrong answer strands a driver.** An EV driver asking where to charge acts on the answer: they leave the motorway for the station they were told about. If that station is full, out of service, slower than stated or does not exist, the cost is a detour, a queue or a battery low enough to limit where they can go next. A price that is wrong turns into a surprise on the bill.

**General-purpose chat models will fill the gap.** Asked for a fast charger in a given city, a language model with no data source can produce a plausible name, power rating and tariff. Range and charge-time questions are arithmetic over battery size, consumption and charger power, which is exactly where a model's answer is hard to check and easy to get subtly wrong.

**Keep the model as the interface.** This project makes the data layer the only source of facts. Station search, availability and route planning are deterministic Python functions the model calls as tools; policy questions go through retrieval over a fixed set of passages. The model chooses tools and phrases the answer. The same functions sit behind plain HTTP endpoints, so the numbers can be checked without the model and keep working when the model provider is down.

## Layer, problem, answer

| Layer       | Problem                                                     | How the project answers it                                                                       |
| ----------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Data        | Station facts must come from somewhere checkable.           | A fixture catalog with OCPI-style fields (`app/data.py`).                                        |
| Core logic  | Energy and range arithmetic is unsafe to leave to a model.  | A deterministic, state-of-charge-aware route planner with a 10% arrival buffer (`app/routing.py`). |
| Retrieval   | Policy questions need a source, not a guess.                | Chroma retrieval over station and policy documents (`app/knowledge.py`).                         |
| Agent       | The model must pick the right source for each question.     | A LangGraph ReAct agent with four tools and a prompt that forbids answering facts without them.  |
| Operability | A model outage should not take the service down.            | Keyless endpoints independent of `/chat`, which returns 503 when the agent fails.                |

## What this is not

- Not a product, and not affiliated with any charging operator.
- Not real data: stations, tariffs, availability and policy text are invented fixtures.
- Not a measured grounding result: no evaluation of the agent's answers exists yet.
- Not deployed: the walkthrough page shows recorded local runs.
