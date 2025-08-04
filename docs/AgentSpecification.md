# Agent Specification

This document describes the specification for the Agent Graph used by the
scalable agent framework.

## Overview

An **AgentGraph** describes how plans and tasks coordinate with each other.
The specification of a graph is provided in a JSON, YAML or Graphviz `dot`
file that resides in a directory.  Each graph directory contains two
sub‑directories:

* `plans/` – python mini projects that implement individual plans.
* `tasks/` – python mini projects that implement individual tasks.

The graph specifier and the `plans/` and `tasks/` directories are siblings.

## Plans

* Each plan has a unique `name`.
* `plan_source` points to the directory under `plans/` containing the
  python project.  A plan project contains a `plan.py` file exposing an entry
  point:

  ```python
  def plan(upstreamResults: TaskResults[]) -> PlanResult:
      ...
  ```
* Each project includes a `requirements.txt` declaring dependencies.
* A plan can have multiple downstream tasks.
* Plans maintain a list of task names that feed into them called
  `upstream_task_ids`.

## Tasks

* Each task has a unique `name`.
* `task_source` points to the directory under `tasks/` containing the python
  project.  A task project contains a `task.py` file exposing an entry point:

  ```python
  def execute(upstreamPlan: PlanResults) -> PlanResult:
      ...
  ```
* Each project includes a `requirements.txt` declaring dependencies.
* A task has exactly one upstream plan.

## Graph Structure

* `AgentGraph` contains:
  * a list of `Plan` instances
  * a list of `Task` instances
  * a map of edges `Plan.name -> List<Task.name>` representing downstream
    tasks
  * a map of edges `Task.name -> Plan.name` representing the single upstream
    plan for a task
* Parsers validate the graph by ensuring:
  * all plans and tasks are connected by at least one edge
  * tasks reference exactly one upstream plan
  * edges reference existing plans and tasks
* Cycles are allowed.

## Parsers

The framework supports pluggable parsers.  The initial implementation uses a
Graphviz `dot` parser (via `org.graphper:graph-support-dot`).  Parsers read a
specifier file and construct the `AgentGraph` along with its `Plan` and `Task`
objects.

