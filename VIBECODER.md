# VIBECODER.md

This file contains lessons learned about working effectively with LLMs while coding. These lessons help human developers become better at collaborating with AI agents on this project.

## LLM Collaboration Lessons

### **Mode Awareness**
- **Always check if you're in Agent mode vs Ask mode**: Agent mode gives the LLM access to tools and allows direct execution. Ask mode only provides information. If you forget to switch modes, the LLM will be unable to perform actions you request.
- **Don't interrupt LLM workflows**: If an LLM is in the middle of a systematic workflow (like issue resolution), let it complete the process rather than interrupting with new requests.

### **Tool Access and Execution**
- **LLMs can run tests directly**: When following test-driven development workflows, LLMs can execute `pytest` commands directly to verify fixes work.
- **LLMs can modify files**: Agent mode allows LLMs to read, write, and modify files directly without asking for permission each time.
- **Trust the workflow**: If you've established a good workflow (like the Real-World Issue Resolution Workflow), trust the LLM to follow it systematically.

### **Communication Patterns**
- **Be explicit about expectations**: When you want an LLM to run tests or execute commands, state it clearly rather than asking "is it ok to...?"
- **Provide confidence estimates**: When LLMs want to run expensive operations (like `motive.main`), they should provide confidence estimates (1-10 scale) with rationale.
- **Accept/reject model**: For expensive operations, use an accept/reject model where the LLM provides the estimate and rationale, then you decide.

### **Workflow Integration**
- **Systematic approaches work better**: LLMs excel at following structured workflows (like the Real-World Issue Resolution Workflow) rather than ad-hoc problem solving.
- **Document lessons immediately**: When LLMs learn something new, they should add it to `AGENT.md` or `VIBECODER.md` immediately to prevent forgetting.
- **Generalize from specific issues**: After fixing a specific problem, LLMs should consider what broader lessons can be learned and documented.

### **Quality Assurance**
- **Test-first approach**: LLMs should write failing tests first, then implement fixes, then verify tests pass.
- **Integration over mocking**: Prefer integration tests with real objects over heavy mocking for better confidence.
- **Full test suite validation**: After any change, run the full test suite to ensure no regressions.

### **Configuration and Field Names**
- **Verify field names in Pydantic models**: When working with configuration, always check the actual field names in the Pydantic model definitions rather than assuming names.
- **Consistency across configs**: Ensure configuration field names match between YAML files and Pydantic models.
- **Test configuration parsing**: Create tests that verify configuration structure is parsed correctly before testing business logic.

### **Error Handling and Debugging**
- **Read error messages carefully**: LLMs should parse error messages thoroughly to understand root causes (e.g., AttributeError about missing fields).
- **Fix root causes, not symptoms**: When errors occur, identify and fix the underlying issue rather than just making tests pass.
- **Use systematic debugging**: Follow structured approaches to debugging rather than random trial and error.

### **Documentation and Knowledge Management**
- **Living documentation**: Keep `AGENT.md` and `VIBECODER.md` updated as lessons are learned.
- **Specific examples**: Include concrete examples and code snippets in documentation rather than abstract principles.
- **Cross-reference related concepts**: Link related lessons and concepts for better discoverability.

### **Project-Specific Patterns**
- **Follow established conventions**: Use existing patterns in the codebase (like `target_player_param` instead of `player_name_param`).
- **Check import paths**: Verify correct import paths by checking where classes are actually defined.
- **Use real constructors**: Build objects with their true signatures so tests mirror production.

## Best Practices for Human-LLM Collaboration

1. **Set clear expectations**: Be explicit about what you want the LLM to do
2. **Trust systematic workflows**: Let LLMs follow established processes
3. **Provide feedback on confidence estimates**: Help LLMs calibrate their confidence levels
4. **Review and approve changes**: Check LLM work before accepting expensive operations
5. **Document lessons learned**: Keep both `AGENT.md` and `VIBECODER.md` updated
6. **Encourage generalization**: Ask LLMs to consider broader lessons from specific fixes

## Common Pitfalls to Avoid

- **Interrupting workflows**: Don't break LLM processes mid-execution
- **Asking for permission repeatedly**: Trust LLMs to follow established patterns
- **Ignoring error messages**: Read and understand errors before proceeding
- **Not documenting lessons**: Let valuable insights get lost
- **Ad-hoc problem solving**: Prefer systematic approaches over random fixes

This file should be updated whenever new insights are gained about effective human-LLM collaboration patterns.
