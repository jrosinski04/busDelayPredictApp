// DropdownComponent.tsx
import React, { useState, useRef, useEffect } from "react";
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  TextInput,
  FlatList,
  TouchableWithoutFeedback,
  Keyboard,
} from "react-native";

const DropdownComponent = ({ data = [], placeholder, onSelect, value }) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const filteredData = data.filter((item) =>
    item.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setQuery(value || "");
  }, [value]);

  const handleSelect = (item) => {
    setQuery(item);
    setIsOpen(false);
    onSelect(item);
    Keyboard.dismiss();
  };

  return (
    <TouchableWithoutFeedback onPress={() => { setIsOpen(false); Keyboard.dismiss(); }}>
      <View style={styles.container}>
        <TextInput
          placeholder={placeholder}
          value={query}
          onFocus={() => setIsOpen(true)}
          onChangeText={(text) => {
            setQuery(text);
            setIsOpen(true);
          }}
          style={styles.inputBox}
        />

        {isOpen && filteredData.length > 0 && (
          <View style={styles.dropdown}>
            <FlatList
              data={filteredData}
              keyExtractor={(item, index) => `${item}-${index}`}
              renderItem={({ item }) => (
                <Pressable
                  onPress={() => handleSelect(item)}
                  style={({ pressed }) => [
                    styles.listItem,
                    pressed && styles.pressedItem,
                  ]}
                >
                  <Text>{item}</Text>
                </Pressable>
              )}
            />
          </View>
        )}
      </View>
    </TouchableWithoutFeedback>
  );
};

const styles = StyleSheet.create({
  container: {
    width: "100%",
    marginBottom: 12,
    zIndex: 999, // ensure it sits on top of other elements
  },
  inputBox: {
    padding: 10,
    borderRadius: 5,
    borderWidth: 1,
    marginBottom: 4,
    backgroundColor: "white",
  },
  dropdown: {
    marginTop: 0,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 5,
    backgroundColor: "white",
    maxHeight: 200,
    zIndex: 1000,
  },
  listItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  pressedItem: {
    backgroundColor: "#ddd",
  },
});

export default DropdownComponent;
