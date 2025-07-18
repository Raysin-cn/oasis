# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
import asyncio
import os

from camel.models import ModelFactory, ModelManager
from camel.types import ModelPlatformType

import oasis
from oasis import (ActionType, LLMAction, ManualAction,
                   generate_twitter_agent_graph)


async def main():
    # NOTE: You need to deploy the vllm server first
    vllm_model_1 = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type="qwen-2",
        # TODO: change to your own vllm server url
        url="http://10.109.28.7:8080/v1",
    )
    vllm_model_2 = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type="qwen-2",
        # TODO: change to your own vllm server url
        url="http://10.109.27.103:8080/v1",
    )

    # Define the models for agents. Agents will select models based on
    # round-robin strategy
    shared_model_manager = ModelManager(
        models=[vllm_model_1, vllm_model_2],
        scheduling_strategy='round_robin',
    )

    # Define the available actions for the agents
    available_actions = ActionType.get_default_twitter_actions()

    agent_graph = await generate_twitter_agent_graph(
        profile_path=("data/twitter_dataset/anonymous_topic_200_1h/"
                      "False_Business_0.csv"),
        model=shared_model_manager,
        available_actions=available_actions,
    )

    # Define the path to the database
    db_path = "./data/twitter_simulation.db"
    os.environ["OASIS_DB_PATH"] = os.path.abspath(db_path)

    # Delete the old database
    if os.path.exists(db_path):
        os.remove(db_path)

    # Make the environment
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=db_path,
    )

    # Run the environment
    await env.reset()

    actions_1 = {}

    actions_1[env.agent_graph.get_agent(0)] = ManualAction(
        action_type=ActionType.CREATE_POST,
        action_args={"content": "Earth is flat."})
    await env.step(actions_1)

    actions_2 = {
        agent: LLMAction()
        # Activate 5 agents with id 1, 3, 5, 7, 9
        for _, agent in env.agent_graph.get_agents([1, 3, 5, 7, 9])
    }

    await env.step(actions_2)

    actions_3 = {}

    actions_3[env.agent_graph.get_agent(1)] = ManualAction(
        action_type=ActionType.CREATE_POST,
        action_args={"content": "Earth is not flat."})
    await env.step(actions_3)

    actions_4 = {
        agent: LLMAction()
        # get all agents
        for _, agent in env.agent_graph.get_agents()
    }
    await env.step(actions_4)

    # Close the environment
    await env.close()


if __name__ == "__main__":
    asyncio.run(main())
