# Testing Scenarios

These scenarios describe manual acceptance checks for v1.

## 1. Start Command

1. Run the bot in long polling mode.
2. Send `/start` from a Telegram account.
3. Verify that the bot replies with a short description of how to request a
   commercial offer.

Expected result: the manager understands that they can send a free-form request
with product names and quantities.

## 2. Refresh Prices

1. Send `/refresh_prices`.
2. Verify that the bot calls the MCP `refresh_prices` tool.
3. Verify that the bot returns the update result or a clear error message.

Expected result: the bot reports whether the 1C price database was updated or
already current.

## 3. Simple Quote Request

1. Send a request such as:
   `ERP корп + сервер мини + клиентская лицензия на 5 мест`
2. Verify that the bot extracts product positions and quantities.
3. Verify that the bot calls MCP quote/search tools.
4. Verify that the bot sends a Markdown commercial offer file.

Expected result: the file contains a table with product code, name, quantity,
price, sum, and total.

## 4. Ambiguous Product

1. Send a request that can match several similar 1C products.
2. Verify that the bot does not silently finalize the wrong product when MCP or
   model output indicates ambiguity.
3. Verify that the bot asks a concise clarification question.
4. Answer the clarification.

Expected result: the bot updates the draft and continues quote generation with
the selected product.

## 5. Markdown File Generation

1. Complete a quote request.
2. Open the generated Markdown file.
3. Verify that it follows the project template.
4. Verify that values in the table match the MCP quote result.

Expected result: the offer is readable, complete, and ready to send or copy into
another document flow.

## 6. Draft Recovery After Restart

1. Start a quote request that requires clarification.
2. Stop the bot process before answering.
3. Start the bot again.
4. Send the clarification answer.

Expected result: the bot restores the existing draft from SQLite and continues
instead of losing the conversation state.
