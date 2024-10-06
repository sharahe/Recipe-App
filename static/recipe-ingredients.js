import { h, render, Component } from "https://esm.sh/preact";
import htm from "https://esm.sh/htm";

// Initialize htm with Preact
export const html = htm.bind(h);

export class Input extends Component {
  onChangeUnit = (ev) => {
    console.log(ev);
    this.props.update(
      this.props.state.name,
      this.props.state.quantity,
      ev.currentTarget.value,
      this.props.index
    );
  };

  onChangeQuantity = (ev) => {
    console.log(ev);
    this.props.update(
      this.props.state.name,
      ev.currentTarget.value,
      this.props.state.unit,
      this.props.index
    );
  };

  onChangeName = (ev) => {
    console.log(ev);
    this.props.update(
      ev.currentTarget.value,
      this.props.state.quantity,
      this.props.state.unit,
      this.props.index
    );
  };

  delete = (ev) => {
    this.props.delete(this.props.index);
  };

  render() {
    return html`<div class="add-ingredient-input">
      <input
        class="ingredient-quantity"
        type="number"
        step="0.01"
        value="${this.props.state.quantity}"
        name="quantity-${this.props.index}"
        onInput=${this.onChangeQuantity}
        placeholder="2"
      />
      <input
        class="ingredient-unit"
        type="text"
        value="${this.props.state.unit}"
        name="unit-${this.props.index}"
        onInput=${this.onChangeUnit}
        placeholder="lb"
      />
      <input
        class="ingredient-name"
        type="text"
        value="${this.props.state.name}"
        name="ingredients-${this.props.index}"
        onInput=${this.onChangeName}
        placeholder="peaches"
      />
      <a onClick=${this.delete} class="margin-left-2 gray">x</a>
    </div>`;
  }
}

export class App extends Component {
  state = { inputs: [{ name: "", unit: "", quantity: Number }] };
  componentDidMount() {
    console.log(this.props);
    this.setState({ inputs: this.props.inputs });
  }

  onClick = (ev) => {
    console.log("clicked", ev);
    this.setState({
      inputs: [...this.state.inputs, { name: "", unit: "", quantity: Number }],
    });
    console.log(this.state.inputs);
  };

  update = (name, quantity, unit, index) => {
    let inputs = [...this.state.inputs];
    inputs[index] = { name, quantity, unit };
    this.setState({ inputs });
  };

  delete = (index) => {
    if (this.state.inputs.length > 1) {
      this.setState({ inputs: this.state.inputs.toSpliced(index, 1) });
    }
  };

  render() {
    return html` <div class="row align-center">
        <label>Ingredients</label>
        <input
          type="hidden"
          name="ingredient-number"
          value="${this.state.inputs.length}"
        />
        <a
          onClick=${this.onClick}
          id="add-ingredient-button"
          class="margin-left-2"
          >+</a
        >
      </div>
      ${this.state.inputs.map((x, i) => {
        return html`<${Input}
          state=${this.state.inputs[i]}
          index=${i}
          update=${this.update}
          delete=${this.delete}
        />`;
      })}`;
  }
}
