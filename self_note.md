# Prompts to ask Claude to revise (not finished yet)

Continue the previous work on dataset generation using Tinker Machine under the Virtual Home simulation environment (currently only text based). Read through the code under the folder data_gen to understand the structure and logic.

A few things that we need to work on to improve the current version of data generation.
1. Currently the tasks that each persona tries is fairly independent. To truly demonstrate the value of EPPS, we want long term dependent tasks that contain rich information about a person's preferences and habits. 
2. Examining the evaluation, currently there is no change in PFS score across the 10 turns, so we need a longer turn for the model to actually observe differences between the RAG approach and our EPPS approach. 
3. The current dataset generation is not diverse. We want a more diverse and realistic human dataset that also contains human pragmatics. 
4. We should try some larger model for the dataset generation since we do have enough compute resources on Tinker to run good LLM inferences.
5. Since you understand how EPPS work by reading through the code logic, carefully evaluate and think about other things that we should try in order to create a more comprehensive and robust dataset targeting our EPPS's long-term functionality.