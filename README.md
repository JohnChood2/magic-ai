# MTG AI Project

This project is focused on creating an AI chatbot for the Magic: The Gathering card game. Users can ask questions to search for cards. Like, "show me all the blue cards that include trees in the artwork."

This project is unofficial Fan Content permitted under the [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy). Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.

## Contents

- [Objective](#objective)
- [Requirements Considerations](#requirements-considerations)
    - [References](#references)
- [Potential Timeline and Milestones](#potential-timeline-and-milestones)
    - [Phase 1](#phase-1)
    - [Phase 2 (or alternative project)](#phase-2-or-alternative-project)
    - [Phase 3](#phase-3)
    - [Other Ideas](#other-ideas)
- [Resources](#resources)
    - [Learn to play Magic](#learn-to-play-magic)
    - [Card Search and Details](#card-search-and-details)
    - [Card Data](#card-data)
    - [Rules](#rules)
    - [Deck Building Sites](#deck-building-sites)
    - [Miscellaneous](#miscellaneous)

### Objective

Create a chatbot interface like ChatGPT where users can ask questions about MTG ("MagicGPT")  
- Specialized in discussing cards (like an AI for [Scryfall's](https://scryfall.com/) advance search)
- Start with a focus on [Commander](https://magic.wizards.com/en/formats/commander) deck building rather than other formats (i.e. Standard, Modern, Pauper, etc.).
- There's a potential, separate, project for [rules](https://magic.wizards.com/en/rules) questions (or should we start here?)
    - Could toggle between card search / deck feeback and rules question context
- Public APIs to comply with the Fan policy
- Guardrails to keep context on Magic. Users should not get advice for other things (i.e. medical advice, etc.) or be able to form a relationship with the agent.

This could potentially become a popular tool if we fully deploy it and keep it live. Similar to [Scryfall](https://scryfall.com/) and [EDHREC](https://edhrec.com/).

Questions:

- How to handle scale and growth? 
- How to pay for servers/resources? What's allowed under the Wizards Fan Content policy (I see Moxfield has a Patreon) --Note that we can use ads, etc. based on the [content policy's rule 1](https://company.wizards.com/en/legal/fancontentpolicy)
    - Should we keep core code private and open source certain things we'd want to highlight, or nothing?
- Do we want the attention that could bring? Positive and negative? Just something to consider.

### Requirements Considerations

- Responses may include images of cards
- Depending on the result set we could immediately display the images to the user in a grid of some form
- If the result set is large, we could display the cards as a bulleted list (with a hover effect that displays the card image)
- The client could cache the API response data (like in a data store like Redux or NgRx potentially) in case the user asks a related question or request (like, "please display the image for card X from the bulleted list"), rather than hitting the API again. (probably more of a nice to have / longer-term feature)

#### References

- See [Scryfall](https://scryfall.com/sets/ecl) results example
- See examples of bulleted lists with and without hover:
    - [Reddit list example - no hover](https://www.reddit.com/r/EDH/comments/tp5tom/comment/i299bp2/)
    - [MTG Salvation example - with hover](https://www.mtgsalvation.com/forums/the-game/casual-multiplayer-formats/162943-must-have-vampire-cards?comment=2)
- See [Moxfield](https://moxfield.com/) and [Archidekt](https://archidekt.com/) for other examples of Magic fan sites
- See [Gatherer](https://gatherer.wizards.com/) the official card database

### Potential Timeline and Milestones

We should focus on iterative development and breaking things down into small tasks as we flesh out the details and next steps. The notes here are just to get us started. Our first major goal should really be focused on a skeleton structure of the most basic requirements (ETL of card data, AI infrastructure and workflows, CI/CD setup, most basic UI and API to support a chatbot as a prototype). Essentially the "hello, world" version of the overall concept which we can add to long-term if we'd like.

#### Phase 1

- Load images and data into DB and train LLM (determine ETL pipeline, [hit Scryfall API](https://scryfall.com/docs/api), use [bulk download](https://scryfall.com/docs/api/bulk-data), etc.)
- AI infrastructure setup and train on card data
    - images (identify objects) and tag them (could consider context for known locations, characters, etc. long-term)
    - keywords, text, colors, and other attributes (card type, power, toughness, etc.) from [Oracle](https://mtg.fandom.com/wiki/Oracle) text
- Setup CI/CD
- Create an API to interact with agent
- Create a UI to interact with the API
- Ask basic questions to get list of cards matching question (i.e. "show me all blue cards with characters in wizard hats")
    - If list of cards is small (4 or less?) display card images
    - If list of cards is long, display in a bulleted list with a hover effect to display images (up to a maximum count, like 20 cards?)
        - How to best paginate card results if there are thousands in the response? (i.e. ["show me all blue cards"](https://scryfall.com/search?as=grid&order=name&q=color%3DU+%28game%3Apaper%29+prefer%3Abest))
        - Pagination within chat bot UI? With what API? Our own or perhaps Srcyfall's?
        - Generate a Scryfall query based on the response and link to their site?

#### Phase 2 (or alternative project)

- Train on the full MTG [rules](https://magic.wizards.com/en/rules) document and [commander rules](https://mtgcommander.net/index.php/rules/)
    - Including card rulings data (see Rulings on the right-hand side of the screen [here](https://gatherer.wizards.com/CMR/en-us/186/jeska-thrice-reborn) as one example)
- UX and other upgrades (i.e. data store on the client for caching some data)

#### Phase 3

- Train on other format rules (i.e. [Pendragon](https://sites.google.com/view/pendragonmtg/basic-rules-guidelines), etc.)
- Could tag cards in DB with formats they're allowed in (is this already in Scryfall's data?)

#### Other ideas

- Public MCP server to our data
- Store chat history (up to X number?)
    - User login and account management
- Allow users to set preferences (potentially globally for all chats or locally within a chat)
    - Such as their favorite types of cards, or the theme they're focused on, etc.
    - Adjust a prompt for the agent based on set preference
- Allow an import of Magic deck lists from [Moxfield](https://moxfield.com/) and [Archidekt](https://archidekt.com/) for AI review
    - Which staple cards to add, which underplayed cards could be interesting to use? (incorporating EDHREC data?)

### Resources

Here is a collection of useful links and resources to learn more. Most are pulled from above to centralize them for easy access.

#### Learn to play Magic

- [How to play Magic: The Gathering (focused on the Standard format)](https://magic.wizards.com/en/how-to-play)
- [How to Play Magic: The Gathering | The Basics](https://www.youtube.com/watch?v=wPF2Rvui7zg)
- [Learn How to Play Commander in Under 5 Minutes! | Good Morning Magic | Zendikar Rising](https://www.youtube.com/watch?v=42noux9KKEM)

#### Card Search and Details

- [Scryfall](https://scryfall.com)
- [Scryfall Syntax](https://scryfall.com/docs/syntax)
- [Scryfall Tagger Tags](https://scryfall.com/docs/tagger-tags)
- [Gatherer](https://gatherer.wizards.com/)
- [EDHREC](https://edhrec.com/)

#### Card Data

- [Scryfall API](https://scryfall.com/docs/api)
- [Scryfall bulk download](https://scryfall.com/docs/api/bulk-data)

#### Rules

- [Commander rules](https://mtgcommander.net/index.php/rules/)
- [Magic rules](https://magic.wizards.com/en/rules)

#### Deck Building Sites

- [Moxfield](https://moxfield.com/)
- [Archidekt](https://archidekt.com/)

#### Miscellaneous

- [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy)
