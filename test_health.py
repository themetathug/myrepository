import asyncio, json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path('mapshock-MVP').resolve()))
from backend.agents.enhanced_orchestration_agent import RobustOrchestrationAgent as R

agent = R({'tavily_api_key': os.getenv('TAVILY_API_KEY', '')})

async def main():
    print('--- initial ---')
    print(json.dumps(agent.get_pipeline_health(), indent=2))
    await asyncio.sleep(35)           # wait for the daemon to tick
    print('--- after 35s ---')
    print(json.dumps(agent.get_pipeline_health(), indent=2))

asyncio.run(main())
