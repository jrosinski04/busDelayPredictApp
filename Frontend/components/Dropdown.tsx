import React, { useState, useEffect } from "react";
import { View, Text, Pressable, StyleSheet, TextInput, FlatList, TouchableWithoutFeedback, Keyboard } from "react-native";

// Dropdown component
const DropdownComponent = ({ data = [], placeholder, onSelect, value }) => {
  
  const [query, setQuery] = useState(""); // Input field state
  const [isOpen, setIsOpen] = useState(false);

  // Filtering data based on user input query
  const filteredData = data.filter((item) =>
    item.toLowerCase().includes(query.toLowerCase())
  );

  // Syncing external value from MainPage
  useEffect(() => {
    setQuery(value || "");
  }, [value]);

  // Handling user selecting an item from the list
  const handleSelect = (item) => {
    setQuery(item);
    setIsOpen(false);
    onSelect(item);
    Keyboard.dismiss();
  };

  // UI rendering of the dropdown menu
  return (
    // Closing dropdown if user taps outside of the dropdown
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

        {/* Dropdown list - only showing if open and there's data */}
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
    zIndex: 999, // ensuring it sits on top of other elements
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
