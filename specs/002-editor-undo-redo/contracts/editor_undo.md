# Contracts: Editor Undo/Redo

Date: 2025-09-09

## Scenarios

1. Undo after typed text

- Given an empty editor
- When I type "G1 X10" then " Y20"
- And I trigger undo
- Then the text becomes "G1 X10"

1. Grouping with separator on Enter

- Given I type "G1 X10"
- And I press Enter (separator)
- And I type "G1 Y20"
- When I trigger undo
- Then the whole last line is undone

1. Redo reapplies

- Given I typed two chunks separated by Enter
- And I undo once
- When I redo
- Then the last chunk is reapplied

1. History cap

- Given maxundo is 2
- When I make 3 separate edits with separators
- Then the first edit is pruned and cannot be undone
